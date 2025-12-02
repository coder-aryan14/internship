# Personal Blog Website

A professional and premium personal blog website built with Flask that allows you to create, view, edit, and manage blog posts through a beautiful web interface.

## Features

- ✨ **Modern & Premium UI** - Beautiful, responsive design with smooth animations
- 📝 **Create Posts** - Write and publish new blog posts with ease
- 👁️ **View Posts** - Browse all posts on the homepage with elegant card layouts
- 🔍 **Search Posts** - Full-text style search across titles and content using SQLite
- 📄 **Pagination** - Professional, paginated listing for large collections of posts
- ✏️ **Edit Posts** - Update existing posts with a user-friendly editor
- 🗂️ **Categories & Tags** - Organize content with categories and keyword-style tags
- 💬 **Comments** - Readers can leave comments on posts
- 👤 **Authentication** - User accounts with login/logout and basic admin role
- 🕒 **Drafts & Scheduling** - Save posts as drafts or schedule them for later
- 📦 **Soft Delete (Archive)** - Archive posts instead of permanently deleting them
- 📈 **Analytics** - Track post views and high-level stats in an admin dashboard
- 📱 **Responsive Design** - Works perfectly on desktop, tablet, and mobile devices
- 🎨 **Professional Styling** - Premium color scheme and typography

## Installation

Since you're not using a virtual environment, install the dependencies directly:

```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask development server:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```

The application will automatically create the SQLite database (`instance/blog.db`) on first run.

## Usage

### Creating a Post

1. Click the "New Post" button in the navigation bar
2. Fill in the title, author (optional), and content
3. Click "Publish Post" to save

### Viewing Posts

- All posts are displayed on the homepage in a grid layout
- Click "Read More" or the post title to view the full post

### Editing a Post

- Click "Edit" on any post card or on the post detail page
- Modify the content and click "Update Post"

### Deleting a Post

- Click "Delete" on any post
- Confirm the deletion in the dialog box

## Project Structure

```
.
├── app.py                 # Main Flask application
├── instance/blog.db      # SQLite database (created automatically)
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── index.html       # Homepage with post listings
│   ├── post_detail.html # Individual post view
│   ├── create_post.html # Create new post form
│   └── edit_post.html   # Edit post form
└── static/              # Static files
    └── style.css        # Premium styling
```

## Technologies Used

- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Flask-Migrate** - Alembic-powered database migrations
- **Flask-Login** - Authentication and user session management
- **SQLite** - Lightweight database
- **HTML5/CSS3** - Modern web standards
- **Inter Font** - Premium typography

## Database Schema

The `Post` model includes:
- `id` - Primary key
- `title` - Post title
- `content` - Post content
- `author` - Legacy author name (defaults to "Admin")
- `author_id` - Foreign key to the `User` table
- `status` - Draft or Published
- `scheduled_for` - Optional datetime to schedule publication
- `is_deleted` - Soft delete flag for archiving posts
- `created_at` - Creation timestamp (indexed for fast ordering)
- `updated_at` - Last update timestamp
- `published_at` - When the post was actually published
- `views` - View counter for analytics
- `category_id` - Foreign key to a `Category`

Related tables:
- `User` - Registered users with hashed passwords and an `is_admin` flag
- `Tag` - Simple keyword tags, many-to-many with posts
- `Category` - High-level content grouping, one-to-many with posts
- `Comment` - Comments linked to posts (and optionally to users)

### Advanced Query & Admin Features

- **Search**: The homepage allows you to search posts by title and content using the search box in the navigation bar.
- **Pagination**: Results are automatically paginated (5 posts per page) with navigation controls for a professional browsing experience.
- **Soft Deletes**: Archived posts are hidden from the public index but preserved in the database.
- **Analytics**: The admin dashboard shows aggregate stats and latest posts with view and comment counts.

## Customization

### Changing the Secret Key

For production use, change the `SECRET_KEY` in `app.py`:

```python
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
```

### Database Migrations

This project is configured with **Flask-Migrate**, so you can evolve the schema safely:

```bash
flask db init      # first time only
flask db migrate   # generate migration scripts from model changes
flask db upgrade   # apply migrations to the SQLite database
```

For local development you can still start from a clean `instance/blog.db` by deleting the file and running the migration commands again.

### Styling

Modify `static/style.css` to customize colors, fonts, and layout. The CSS uses CSS variables for easy theming.

## License

This project is open source and available for personal use.

