# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
Existing Python package (`src/sony_alpha_viet/`) renders each blog post from Markdown + YAML frontmatter into static HTML/CSS: a standalone page and an `<article>` block for pasting into a CMS. No front-end framework.

## Users
Vietnamese readers of the AlphaColorlab.com blog, on phone and desktop:
- people about to buy or who just bought a Sony Alpha camera, choosing a body or lens;
- students of a Sony Camera Trainer, re-reading a lesson or looking up a menu setting after class;
- semi-pro shooters who know the basics and want tips, workflow and colour.

The writer is the trainer (Thai Pham), who drafts in Markdown/Obsidian with Claude and publishes.

## Product Purpose
Vietnamese articles about Sony Alpha cameras that answer one question fast (TL;DR, direct answers under each heading, comparison tables, FAQ) and teach the reader to do it on their own camera. Success: the reader gets the answer in the first screen, finds the menu item on the camera, and trusts the source.

## Positioning
Written by a Sony Camera Trainer, with menu names taken from Sony's approved Vietnamese menu translation memory, not guessed translations.

## Operating Context
Readers arrive from Google / AI answers / Zalo / Facebook links, mostly on phones. Posts carry tables (spec comparisons), step lists, checklists, FAQ, sources, JSON-LD (Article, FAQPage, HowTo).

## Capabilities and Constraints
- Vietnamese text with stacked diacritics (ấ, ặ, ữ, Ỗ…) must render without clipping or collision, including in headings and uppercase.
- Body font: Noto Sans (user-pinned).
- Specs and prices not verified against Sony are marked `[cần xác minh]` in drafts; the site refuses the marker, so every one is resolved or cut before export.

## Brand Commitments
- Site: AlphaColorlab.com. Its design system (`DESIGN.md`, `CLAUDE.md`, `packages/colorlab-tokens` in github.com/thaikpham/alphacolorlab.com) is the visual authority; blog HTML inherits the `/blog` paper theme and its 10-block article model — no separate visual world here.
- Golden rule for all copy: protect Sony; never conclude a competitor is better than Sony.
- Voice: plain Vietnamese, no machine-translation tone (see `skills/sony-alpha-viet/references/writing-style-vi.md`).

## Evidence on Hand
- Sample post: `skills/sony-alpha-viet/examples/example-blog-post.md`.
- Template: `skills/sony-alpha-viet/templates/blog-post-template.md`.
- Logo, palette, fonts and article components live in the site repo; no photography yet; do not invent testimonials, prices or benchmarks.

## Product Principles
1. Answer first, explain after.
2. The reader must be able to act on the camera: menu names in Vietnamese OSD with the English name in brackets.
3. Trust over hype: sources visible, unverified facts flagged.

## Accessibility & Inclusion
Mobile-first reading; WCAG AA contrast; `lang="vi"`; readable at 200% zoom.
