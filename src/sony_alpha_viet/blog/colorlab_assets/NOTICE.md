# Alpha ColorLab assets (used by `colorlab_html.py`)

- `NotoSans-latin.woff2`, `NotoSans-vietnamese.woff2` — Noto Sans, © Google, SIL Open Font License 1.1.
  Copied from `public/fonts/noto-sans/` in [thaikpham/alphacolorlab.com](https://github.com/thaikpham/alphacolorlab.com)
  (`npm run fonts:vendor` there; latin + vietnamese subsets, weights 400–800).
- `site.css` — the site's compiled stylesheet, pruned to the classes the renderer emits. Generated, never hand-edited.
  After the site's design changes, start it (`npm run dev`, offline seed mode is fine) and run:

      uv run python -m sony_alpha_viet.blog.colorlab_html sync http://localhost:3000/vi/blog/back-button-af
