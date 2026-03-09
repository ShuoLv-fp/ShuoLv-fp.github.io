# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development
- **Start local server**: `bash run_server.sh` or `ruby start_jekyll.rb` or `bundle exec jekyll serve`
- **Install dependencies**: `bundle install`
- **Build site**: `bundle exec jekyll build`

### Alternative Development Scripts
- `run_server.sh` contains: `bundle exec jekyll liveserve` (Note: should be `serve`, not `liveserve`)
- `start_jekyll.rb` forces EventMachine pure Ruby implementation and runs `bundle exec jekyll serve`
- CLAUDE.md is excluded from Jekyll processing to avoid build errors

## Architecture Overview

This is a Jekyll-based academic personal homepage built on the AcadHomepage template. Key architectural components:

### Core Structure
- **Jekyll Static Site Generator**: Uses Ruby/Jekyll with GitHub Pages deployment
- **Sass Styling**: Custom styles in `_sass/` directory with responsive design
- **Modular Content**: Page content split into reusable includes in `_pages/includes/`
- **Automated Google Scholar Integration**: Python crawler updates citation data automatically

### Key Directories
- `_pages/`: Main content pages (about.md, blog.md, etc.)
- `_pages/includes/`: Modular content sections (education.md, research_interests.md, etc.)
- `_layouts/`: HTML templates (default.html)
- `_includes/`: Reusable components (masthead.html, sidebar.html, etc.)
- `_sass/`: Sass/SCSS stylesheets
- `assets/`: Static assets (CSS, JS, images, files)
- `google_scholar_crawler/`: Python script for fetching Google Scholar data

### Configuration
- **Main config**: `_config.yml` contains site settings, author info, and Jekyll configuration
- **Dependencies**: `Gemfile` specifies Jekyll and plugin dependencies
- **GitHub Actions**: `.github/workflows/pages.yml` handles automated deployment to GitHub Pages

### Content Management
- Homepage content is in `_pages/about.md`
- Content is modularized using Jekyll includes: `{% include_relative includes/research_interests.md %}`
- Google Scholar citations can be displayed using: `<span class='show_paper_citations' data='SCHOLAR_PAPER_ID'></span>`
- **Content Update Pattern**: Major sections (News, Publications, Teaching) are in separate include files for easy maintenance
- **Styling for Notices**: Use colored highlight boxes for important announcements:
  ```html
  <span style="color: #E74C3C; background-color: rgba(231, 76, 60, 0.1); padding: 5px 10px; border-radius: 4px;">Important announcement</span>
  ```

### Automated Features
- Google Scholar citation tracking via `google_scholar_crawler/main.py`
- GitHub Actions deployment pipeline
- Responsive design with dark mode support (`_sass/_dark-mode.scss`)

### Social Media Integration
- Social media links are configured in `_config.yml` under the `author` section
- Sidebar social icons are rendered via `_includes/author-profile.html`
- Two versions: full sidebar (with text) and compact mobile (icons only)
- WeChat QR code integration: set `wechat: "path/to/qr-image.jpg"` in config
- Uses Font Awesome icons (e.g., `fab fa-fw fa-weixin` for WeChat)

### Publications and Projects Management
- **Publications structure**: Journal Articles → Conference Papers → Working Projects
- Working Projects section describes ongoing research without formal publication status
- When papers get accepted, move from Working Projects to appropriate published section
- AMIA, ICLR, and other conference papers go under Conference Papers

### Homepage Maintenance Guidelines
- Update `_pages/includes/news.md` regularly with latest achievements
- Maintain "Last updated" timestamp at bottom of `_pages/about.md`
- For major life events (degree completion, new positions), update both News and relevant sections
- Use consistent date format: [YYYY.MM] for news entries
- **Multi-section updates**: When adding degrees, update both Education section and News section
- **Publication workflow**: Move papers from Working Projects to Conference/Journal sections when accepted
- **Important notices**: Use colored highlight boxes for collaboration requests, job seeking, etc.

### Site Configuration Notes
- Site title: "Xiaolong Luo | Harvard Ph.D. Student"
- Repository: "AaronLuo00/AaronLuo00.github.io"
- Base URL: ""
- Google Analytics and SEO configured
- CLAUDE.md is excluded from Jekyll processing in `_config.yml`
