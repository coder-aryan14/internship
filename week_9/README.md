# Personal Blog Website

A professional and premium personal blog website built with Flask that allows you to create, view, edit, and manage blog posts through a beautiful web interface.

## Features

- ✨ **Modern & Premium UI** - Beautiful, responsive design with smooth animations
- 📝 **Create Posts** - Write and publish new blog posts with ease
- 👁️ **View Posts** - Browse all posts on the homepage with elegant card layouts
- ✏️ **Edit Posts** - Update existing posts with a user-friendly editor
- 🗑️ **Delete Posts** - Remove posts with confirmation dialogs
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

The application will automatically create the SQLite database (`blog.db`) on first run.

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
├── blog.db               # SQLite database (created automatically)
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
- **SQLite** - Lightweight database
- **HTML5/CSS3** - Modern web standards
- **Inter Font** - Premium typography

## Database Schema

The `Post` model includes:
- `id` - Primary key
- `title` - Post title
- `content` - Post content
- `author` - Author name (defaults to "Admin")
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## Customization

### Changing the Secret Key

For production use, change the `SECRET_KEY` in `app.py`:

```python
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
```

### Styling

Modify `static/style.css` to customize colors, fonts, and layout. The CSS uses CSS variables for easy theming.

## License

This project is open source and available for personal use.

