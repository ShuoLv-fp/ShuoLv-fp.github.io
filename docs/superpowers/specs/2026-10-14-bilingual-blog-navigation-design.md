# Bilingual Blog Navigation Design

## Goal

Add a clear Blog entry to both language variants of the academic homepage so visitors can reach the public Field Notes site at `/lsBlog/`.

## Navigation

- Add `Blog` to the English primary navigation in `_data/navigation.yml`.
- Add `博客` to the Chinese primary navigation in `_data/navigation-zh.yml`.
- Place each entry immediately after `Paper Feed` or `学术速递`, keeping the information-oriented destinations together.
- Link directly to `/lsBlog/` and use the existing same-tab behavior for internal URLs.

The existing greedy navigation component will continue to handle narrow viewports and overflow. No new styling or template branching is required.

## Compatibility

The legacy `_pages/blog.md` redirect remains unchanged. The new navigation entries bypass that stale route and point directly to the current blog location.

## Testing

Add a source-level regression test that verifies:

- both language navigation files contain exactly one blog entry;
- the labels are localized as `Blog` and `博客`;
- both entries use `/lsBlog/`;
- each entry follows its language's paper-feed item.

Run the focused navigation test, the complete Python test suite, and a Jekyll production build.
