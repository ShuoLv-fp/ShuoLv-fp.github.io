# Shuo Lv — Academic Personal Homepage

Academic personal homepage of Shuo Lv (吕烁), a Master's student at Beijing Institute of Technology working on computational neuroscience, large language models, and complex networks. The site is built with [AcadHomepage](https://github.com/RayeRen/acad-homepage.github.io) (Jekyll + GitHub Pages).

## Structure

- `_pages/about.md` — English homepage (`/`)
- `_pages/zh.md` — Chinese homepage (`/zh/`), with a one-click language switch in the navigation bar
- `_pages/paper-feed.md` / `_pages/paper-feed-zh.md` — bilingual seven-day paper feed (`/paper-feed/` and `/zh/paper-feed/`)
- `_pages/includes/` — English section contents (Education, Publications, News, Projects, etc.)
- `_pages/includes/zh/` — Chinese section contents (mirror of the English sections)
- `_data/navigation.yml` / `_data/navigation-zh.yml` — English / Chinese navigation
- `images/pub/` — publication figure thumbnails
- `assets/data/paper-feed.json` — validated public paper-feed data
- `.github/workflows/paper-feed.yml` — daily and manual paper-feed updates

## Maintenance Notes

- Keep the English (`includes/`) and Chinese (`includes/zh/`) sections in sync when updating content.
- Paper titles, author lists, and journal names stay in English in both languages; only narrative text is translated.
- Paper-feed credentials belong only in GitHub Actions Secrets. Follow the [paper-feed operations guide](docs/paper-feed-operations.md) for preview, publishing, credential rotation, and recovery.

## Local Development

```bash
bash run_server.sh
# or
bundle exec jekyll serve
```

Then open http://127.0.0.1:4000.
