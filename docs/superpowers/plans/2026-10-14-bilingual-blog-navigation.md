# Bilingual Blog Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a localized primary-navigation entry on both homepage language variants that links directly to `/lsBlog/`.

**Architecture:** Keep navigation ownership in the existing English and Chinese YAML data files so `_includes/masthead.html` renders the new entries through its established loop. Add one source-level regression test that treats each paper-feed item and its following blog entry as an ordered pair.

**Tech Stack:** Jekyll, Liquid, YAML navigation data, Python `unittest`

## Global Constraints

- English copy is `Blog`; Chinese copy is `博客`.
- Both entries link directly to `/lsBlog/` in the current tab.
- Each entry appears immediately after `Paper Feed` or `学术速递`.
- Do not change `_includes/masthead.html`, `_pages/blog.md`, or navigation styling.

---

### Task 1: Add the bilingual Blog navigation entries

**Files:**
- Modify: `tests/test_homepage_presentation.py`
- Modify: `_data/navigation.yml`
- Modify: `_data/navigation-zh.yml`

**Interfaces:**
- Consumes: `_includes/masthead.html` reads `site.data.navigation.main` for English and `site.data['navigation-zh'].main_zh` for Chinese.
- Produces: one internal navigation item per language with URL `/lsBlog/`.

- [ ] **Step 1: Write the failing navigation contract test**

Append this method to `HomepagePresentationTests` in `tests/test_homepage_presentation.py`:

```python
    def test_bilingual_navigation_links_to_field_notes_blog(self):
        for path, feed_title, feed_url, blog_title in (
            (
                Path("_data/navigation.yml"),
                "Paper Feed",
                "/paper-feed/",
                "Blog",
            ),
            (
                Path("_data/navigation-zh.yml"),
                "学术速递",
                "/zh/paper-feed/",
                "博客",
            ),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                expected = (
                    f"  - title: '{feed_title}'\n"
                    f"    url: '{feed_url}'\n\n"
                    f"  - title: '{blog_title}'\n"
                    "    url: '/lsBlog/'"
                )
                self.assertIn(expected, text)
                self.assertEqual(text.count(f"title: '{blog_title}'"), 1)
                self.assertEqual(text.count("url: '/lsBlog/'"), 1)
```

- [ ] **Step 2: Run the focused test and verify the red state**

Run:

```bash
python3 -m unittest \
  tests.test_homepage_presentation.HomepagePresentationTests.test_bilingual_navigation_links_to_field_notes_blog \
  -v
```

Expected: `FAIL` because neither navigation file contains the new blog entry.

- [ ] **Step 3: Add the minimal English navigation entry**

In `_data/navigation.yml`, place this block immediately after the `Paper Feed` item:

```yaml
  - title: 'Blog'
    url: '/lsBlog/'
```

- [ ] **Step 4: Add the minimal Chinese navigation entry**

In `_data/navigation-zh.yml`, place this block immediately after the `学术速递` item:

```yaml
  - title: '博客'
    url: '/lsBlog/'
```

- [ ] **Step 5: Run the focused test and verify the green state**

Run:

```bash
python3 -m unittest \
  tests.test_homepage_presentation.HomepagePresentationTests.test_bilingual_navigation_links_to_field_notes_blog \
  -v
```

Expected: `OK` with one passing test.

- [ ] **Step 6: Run complete verification**

Run:

```bash
python3 -m unittest discover -s tests -v
bundle exec jekyll build
git diff --check
```

Expected: the full Python suite passes, Jekyll exits with status 0, and `git diff --check` prints no errors.

- [ ] **Step 7: Commit the implementation**

```bash
git add tests/test_homepage_presentation.py \
  _data/navigation.yml \
  _data/navigation-zh.yml
git commit -m "feat: add bilingual blog navigation"
```
