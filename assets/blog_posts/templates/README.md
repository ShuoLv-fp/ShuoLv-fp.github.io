# Blog Post Template Usage Guide

This template provides a standardized structure for creating new blog posts with a clean, responsive design and dark mode support.

## How to Use

1. Create a new HTML file in the `assets/blog_posts/` directory
2. Copy the content from `blog-post-template.html`
3. Replace the following placeholders:
   - `{{TITLE}}` - Your blog post title
   - `{{DATE}}` - Publication date (e.g., "March 10, 2024")
   - `{{CONTENT}}` - Your blog post content

## Features

- Responsive design (max-width: 1200px)
- Dark mode support with theme toggle
- Navigation buttons (Home and Blog)
- Clean typography and spacing
- Support for:
  - Headers (h1, h2)
  - Lists (ul, ol)
  - Images with captions
  - Code blocks
  - Links
  - SVG graphics

## Example Content Structure

```html
<div class="content">
    <!-- For images -->
    <div class="image-container">
        <img src="path/to/image.jpg" alt="Description">
        <div class="caption">Image caption here</div>
    </div>

    <!-- For code blocks -->
    <pre><code>
    your code here
    </code></pre>

    <!-- For lists -->
    <ul>
        <li>List item 1</li>
        <li>List item 2</li>
    </ul>
</div>
```

## Theme Support

The template includes built-in dark mode support. The theme toggle button is positioned in the top-right corner. The selected theme persists across page reloads using localStorage.

## CSS Variables

You can customize the colors by modifying the CSS variables in the `:root` and `[data-theme="dark"]` selectors:

```css
:root {
    --bg-color: #f8f9fa;
    --text-color: #2c3e50;
    --article-bg: white;
    /* ... other variables ... */
}

[data-theme="dark"] {
    --bg-color: #1a1a1a;
    --text-color: #e0e0e0;
    --article-bg: #2d2d2d;
    /* ... other variables ... */
}
