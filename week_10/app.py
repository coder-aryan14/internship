from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from sqlalchemy import event
from sqlalchemy.engine import Engine

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-change-this-in-production"

# Ensure a dedicated instance directory for the SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, "blog.db")

# SQLite database configuration using an absolute path for reliability
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "error"


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Apply recommended pragmas on SQLite for more robust behavior in production-like setups.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


### Database Models

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship("Post", back_populates="author_user", lazy="dynamic")
    comments = db.relationship("Comment", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

    posts = db.relationship(
        "Post",
        secondary=post_tags,
        back_populates="tags",
    )

    def __repr__(self):
        return f"<Tag {self.name}>"


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)

    posts = db.relationship("Post", back_populates="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # author name kept for legacy UX, but link to a User when authenticated
    author = db.Column(db.String(100), default="Admin")
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    status = db.Column(db.String(20), default="published", index=True)  # draft/published
    scheduled_for = db.Column(db.DateTime, nullable=True, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    published_at = db.Column(db.DateTime, nullable=True, index=True)

    views = db.Column(db.Integer, default=0)

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    author_user = db.relationship("User", back_populates="posts")
    category = db.relationship("Category", back_populates="posts")
    tags = db.relationship(
        "Tag",
        secondary=post_tags,
        back_populates="posts",
    )
    comments = db.relationship("Comment", back_populates="post", lazy="dynamic")

    def publish(self):
        self.status = "published"
        if self.published_at is None:
            self.published_at = datetime.utcnow()

    def soft_delete(self):
        self.is_deleted = True

    def __repr__(self):
        return f"<Post {self.title}>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    author_name = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    post = db.relationship("Post", back_populates="comments")
    user = db.relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<Comment {self.author_name}: {self.body[:20]}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.route("/")
def index():
    """
    Home page with advanced features:
    - Only shows non-deleted posts that are published or scheduled in the past
    - Full-text style search on title and content
    - Pagination for large numbers of posts
    """
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "", type=str).strip()

    now = datetime.utcnow()
    query = Post.query.filter(
        Post.is_deleted.is_(False),
        db.or_(
            Post.status == "published",
            db.and_(Post.status == "draft", Post.scheduled_for <= now),
        ),
    )

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(Post.title.ilike(like_pattern), Post.content.ilike(like_pattern))
        )

    query = query.order_by(Post.created_at.desc())

    per_page = 5
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "index.html",
        posts=pagination.items,
        pagination=pagination,
        search_query=search_query,
    )

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    post = Post.query.filter_by(id=post_id, is_deleted=False).first_or_404()

    # Increment views for analytics
    post.views = (post.views or 0) + 1
    db.session.commit()

    # Handle new comment submission
    if request.method == "POST":
        author_name = request.form.get("author_name") or (
            current_user.username if current_user.is_authenticated else "Anonymous"
        )
        body = request.form.get("body", "").strip()

        if not body:
            flash("Comment body is required.", "error")
            return redirect(url_for("post_detail", post_id=post.id))

        comment = Comment(
            post=post,
            user=current_user if current_user.is_authenticated else None,
            author_name=author_name,
            body=body,
        )
        db.session.add(comment)
        db.session.commit()
        flash("Comment added.", "success")
        return redirect(url_for("post_detail", post_id=post.id))

    comments = (
        post.comments.order_by(Comment.created_at.asc()).all()
        if post.comments is not None
        else []
    )
    return render_template("post_detail.html", post=post, comments=comments)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        author_name = request.form.get("author", "").strip() or current_user.username
        status = request.form.get("status", "published")
        scheduled_for_raw = request.form.get("scheduled_for", "").strip()
        category_name = request.form.get("category", "").strip()
        tags_raw = request.form.get("tags", "").strip()

        if not title or not content:
            flash("Title and content are required!", "error")
            return redirect(url_for("create_post"))

        scheduled_for = None
        if scheduled_for_raw:
            try:
                scheduled_for = datetime.fromisoformat(scheduled_for_raw)
            except ValueError:
                flash("Invalid schedule date/time format.", "error")
                return redirect(url_for("create_post"))

        post = Post(
            title=title,
            content=content,
            author=author_name,
            author_id=current_user.id,
            status=status,
            scheduled_for=scheduled_for,
        )

        if status == "published" and (scheduled_for is None or scheduled_for <= datetime.utcnow()):
            post.publish()

        # Category
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
            post.category = category

        # Tags (comma-separated)
        if tags_raw:
            tag_names = {t.strip().lower() for t in tags_raw.split(",") if t.strip()}
            for name in tag_names:
                tag = Tag.query.filter_by(name=name).first()
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                post.tags.append(tag)

        db.session.add(post)
        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for("index"))

    return render_template("create_post.html")


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if not (current_user.is_admin or post.author_id == current_user.id):
        abort(403)

    if request.method == "POST":
        post.title = request.form.get("title", "").strip()
        post.content = request.form.get("content", "").strip()
        post.author = (
            request.form.get("author", "").strip() or post.author or current_user.username
        )
        status = request.form.get("status", post.status)
        scheduled_for_raw = request.form.get("scheduled_for", "").strip()
        category_name = request.form.get("category", "").strip()
        tags_raw = request.form.get("tags", "").strip()
        post.updated_at = datetime.utcnow()

        if not post.title or not post.content:
            flash("Title and content are required!", "error")
            return redirect(url_for("edit_post", post_id=post_id))

        scheduled_for = None
        if scheduled_for_raw:
            try:
                scheduled_for = datetime.fromisoformat(scheduled_for_raw)
            except ValueError:
                flash("Invalid schedule date/time format.", "error")
                return redirect(url_for("edit_post", post_id=post_id))

        post.status = status
        post.scheduled_for = scheduled_for

        if status == "published" and (scheduled_for is None or scheduled_for <= datetime.utcnow()):
            post.publish()

        # Category
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
            post.category = category
        else:
            post.category = None

        # Tags
        post.tags.clear()
        if tags_raw:
            tag_names = {t.strip().lower() for t in tags_raw.split(",") if t.strip()}
            for name in tag_names:
                tag = Tag.query.filter_by(name=name).first()
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                post.tags.append(tag)

        db.session.commit()
        flash("Post updated successfully!", "success")
        return redirect(url_for("post_detail", post_id=post.id))

    tags_value = ", ".join(tag.name for tag in post.tags)
    category_value = post.category.name if post.category else ""

    return render_template(
        "edit_post.html",
        post=post,
        tags_value=tags_value,
        category_value=category_value,
    )


@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if not (current_user.is_admin or post.author_id == current_user.id):
        abort(403)

    post.soft_delete()
    db.session.commit()
    flash("Post moved to archive.", "success")
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)

    total_posts = Post.query.filter_by(is_deleted=False).count()
    total_views = db.session.query(db.func.sum(Post.views)).scalar() or 0
    total_comments = Comment.query.count()

    latest_posts = (
        Post.query.filter_by(is_deleted=False)
        .order_by(Post.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin_dashboard.html",
        total_posts=total_posts,
        total_views=total_views,
        total_comments=total_comments,
        latest_posts=latest_posts,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username_or_email = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username_or_email or not password:
            flash("Username/email and password are required.", "error")
            return redirect(url_for("login"))

        user = User.query.filter(
            db.or_(
                User.username == username_or_email,
                User.email == username_or_email,
            )
        ).first()

        if not user or not user.check_password(password):
            flash("Invalid credentials.", "error")
            return redirect(url_for("login"))

        login_user(user, remember=True)
        flash("Logged in successfully.", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("index"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm", "").strip()

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if User.query.filter(
            db.or_(User.username == username, User.email == email)
        ).first():
            flash("Username or email already taken.", "error")
            return redirect(url_for("register"))

        user = User(username=username, email=email)
        user.set_password(password)

        # First user becomes admin for convenience
        if User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

