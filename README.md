# Sony Alpha Việt (alphaskill)

Rules, a glossary and tools that let an AI translate Sony Alpha camera menus and documents into natural Vietnamese, check every string the way a human editor would, and write camera blog posts that rank in search and get quoted by AI answers.

**Author:** Pham Khang Thai · **Version:** 1.4.0 · **License:** MIT · **Python:** 3.10+

## What it does

| Mode | Input | Output |
|---|---|---|
| A · Menu translation | English/Japanese menu strings, Sony `*_TranslationCheck_VN.xls` files | Vietnamese strings that fit the on-screen frame, short forms for narrow frames, Sony files with the proposal columns (AN/AU/AV) filled |
| B · Document translation | Help Guides, manuals, product copy (PDF, DOCX, HTML) | Natural Vietnamese prose, menu names in bold with the English name, list of terms used |
| C · Blog (SEO + AIO) | A keyword and an audience, or a finished draft | Post with TL;DR, comparison table, FAQ, JSON-LD; a 40-point score and a fix list |
| D · Trainer | Student questions, lesson plans | Answers from a photography knowledge base, lesson plans, exercises |

## How it works

One source of truth feeds every surface:

- **Rules and workflow** live in [`skills/sony-alpha-viet/`](skills/sony-alpha-viet/) (`SKILL.md` plus references).
- **Data** (glossary, replacement rules, banned words, keep-English list, translation memory, knowledge notes) lives in a data folder. The public subset is [`data-sample/`](data-sample/) (698 glossary entries, 176 replacement rules, 29 knowledge notes, empty translation memory).
- **Engine** is the Python package [`src/sony_alpha_viet/`](src/sony_alpha_viet/): an MCP server with 47 tools, 3 prompts (`translate_menu`, `write_blog`, `audit_post`) and the references as resources.
- **Bundles** for chat apps (`llms-full.txt`, `llms-blog.txt`, `llms-knowledge.txt`, `portable/`) are generated from the skill and data by `scripts/build_portable.py`, so every AI reads the same rules.

## Pick a surface

| Surface | Setup | Glossary + rules | Frame-width check | Reads/writes Sony `.xls` | Remembers fixes |
|---|---|---|---|---|---|
| Paste one link into any chat AI | None | Yes | No | No | No |
| Custom GPT, Gemini Gem, Meta AI Studio | Upload files once | Yes | No | No | No |
| Public API `api.alphacolorlab.com` | None | Yes | Yes | No | No |
| Claude Code plugin or Gemini CLI extension | ~2 minutes | Yes | Yes | Yes | Yes |
| Local Llama agent (Ollama or Llama API) | Python + model | Yes | Yes | Optional | Optional |

Real Sony translation projects need the Claude Code or Gemini CLI install: only that has translation memory, frame-width checks and Sony file output.

### Paste a link (any AI)

```
Read https://raw.githubusercontent.com/thaikpham/alphaskill/main/llms-full.txt and follow its instructions. Then: [your request]
```

Add `llms-blog.txt` for blog work or `llms-knowledge.txt` for trainer work. The AI gets text only: it cannot measure frames, open `.xls` files or remember corrections, and it marks unverified specs and prices `[cần xác minh]` instead of guessing.

### Custom GPT, Gem, Meta AI Studio

Paste `portable/system-prompt.md` into Instructions and upload `portable/knowledge/`. Per-platform steps: [portable/README.md](portable/README.md).

### Claude Code

```
/plugin marketplace add thaikpham/alphaskill
```

```
/plugin install sony-alpha-viet@alphaskill
```

Restart Claude Code, run `/mcp` and check that `sony-alpha-viet` is connected.

### Gemini CLI

```bash
gemini extensions install https://github.com/thaikpham/alphaskill
```

### Public API

`https://api.alphacolorlab.com` is read-only, needs no account and serves `data-sample/`.

- `GET /v1`: version, data counts, the 28 read-only tools and their parameters
- `GET /v1/lookup_term?text=Focus%20Area`
- `POST /v1/check_translation` with `{"en": "Focus Area", "vi": "Vùng lấy nét"}`
- MCP clients: add `https://api.alphacolorlab.com/mcp`

### Local Llama agent

```bash
uv run sony-alpha-viet-llama "Translate for the A7 IV menu: Focus Area, Silent Mode"
```

Defaults to Ollama `llama3.2:3b` with a small read/check tool set. `--base-url` and `--model` switch to Meta's Llama API (`LLAMA_API_KEY`); `--tools` picks other tools; `--allow-write` starts the server with its write tools (memory, `.xls`).

## Using it at scale

1. **Whole Sony file sets, not single strings.** `xls_review(folder)` scores every row of every `*TranslationCheck_VN.xls` in a folder (rule errors, frame overflow, locked terms, drift from memory, the same English translated differently) and can export all findings to CSV. `prepare_batch` pulls memory matches and glossary terms for a list of strings in one call. `xls_write` fills only the AN/AU/AV columns of a copy, keeps every other byte, and never overwrites the original.
2. **Four-persona cross-check before delivery.** Menu translation runs four reviewer personas as sub-agents (Sony Vietnam product specialist, photo-media editor, long-time Alpha user, multi-brand photographer). Changes need 3 of 4 votes; locked terms and user-approved memory win. Workflow and prompts: [`persona-review.md`](skills/sony-alpha-viet/references/persona-review.md), [`templates/persona-review/`](templates/persona-review/).
3. **Human review on unique pairs only.** `python -m sony_alpha_viet.xls.review_pairs <folder> <out.xlsx> <mapping.json>` collapses a file set into unique English | Vietnamese pairs (thousands of rows become one sheet a team can edit) plus a mapping from each pair to its rows, so the team's edits can be applied back to every file.
4. **Every approved fix is reused.** `record_term`, `remember_translation`, `ban_term` and `keep_english` store decisions; `learn` turns repeated corrections into replacement rules; `commit_memory` commits the data folder to git so every change has history; `consistency_report` lists strings that drifted into several translations.
5. **One rule set for a whole team.** The same skill and data drive Claude Code, Gemini CLI, the API, chat bundles and Obsidian (`obsidian_export` / `obsidian_import`). `scripts/publish.sh` moves vault edits into the data folder, exports the public subset with `scripts/export_public_data.py` and ships it to the API.

Blog teams get the same leverage: `blog_audit` scores a draft on all 40 checklist items in one read-only call, so it can gate posts in a CMS or CI; `colorlab_article`, `colorlab_html` and `colorlab_pack` turn a Markdown post into an Alpha ColorLab page or content pack.

## MCP tools (46)

| Area | Tools |
|---|---|
| Data, guidelines | `data_info`, `get_guidelines` |
| Menu translation | `lookup_term`, `search_memory`, `prepare_batch`, `check_translation`, `check_fit`, `suggest_short`, `consistency_report` |
| Sony `.xls` files | `xls_read`, `xls_review`, `xls_write`, `xls_apply_agreed` |
| Memory and learning | `record_term`, `record_feedback`, `remember_translation`, `ban_term`, `keep_english`, `learn`, `review_memory`, `disable_rule`, `commit_memory` |
| Sony documents | `lookup_prose_term`, `ingest_docs`, `ingest_helpguide`, `search_docs`, `docs_term_report` |
| Blog SEO + AIO | `slugify`, `count_words`, `style_lint`, `seo_audit`, `aio_audit`, `paa_generator`, `citation_checker`, `freshness_check`, `brand_voice_checker`, `blog_audit`, `faq_schema` |
| Alpha ColorLab publishing | `colorlab_article`, `colorlab_html`, `colorlab_pack` |
| Trainer knowledge | `search_knowledge`, `get_knowledge`, `add_knowledge` |
| Obsidian | `obsidian_export`, `obsidian_import`, `obsidian_audit_note` |

18 tools write data or touch local files. They are removed with `--read-only`, on any non-loopback host, and on the public API, which leaves 28.

What the checks do:

- `check_translation`: leftover English, banned words, clipped abbreviations, `${v1}` variables and `<cE660>` icons, consistency with memory, and on-screen width measured with font metrics (Liberation Sans by default, `SONY_VN_FONT` to override). Width is an estimate; Sony's own tool has the final say.
- `ingest_docs`: loads Sony Vietnamese PDFs/DOCX, converts legacy VNI fonts to Unicode and drops duplicates; `ingest_helpguide` loads an English Help Guide from its index URL. `search_docs` then shows how Sony itself phrased something.

## Data

| Data | Where | Public |
|---|---|---|
| Glossary, rules, exceptions, published knowledge notes | `data-sample/` | Yes |
| Translation memory, ingested Sony documents, project archives | private repo `alphaskill-data` | No |

The server picks the data folder in this order: `$SONY_VN_DATA`, then `"data"` in `~/.config/sony-alpha-viet/config.json`, then `~/.local/share/sony-alpha-viet/data` (created from the sample on first use). Without private data, glossary lookup and every check still work; translation memory and Sony document search start empty.

## Hard limits

- Text only. The tools never modify, repack or flash camera firmware and never enable service mode.
- No invented specs, prices or release dates: unverified facts are marked `[cần xác minh]` and the audits treat the post as incomplete.
- Sony originals are never overwritten; output always goes to a copy.

## Development

```bash
uv sync
```

```bash
uv run pytest -q
```

```bash
uv run python scripts/build_portable.py
```

- Edit rules in `skills/sony-alpha-viet/` and data in `data-sample/`; never edit `llms-*.txt` or `portable/knowledge/` by hand. `build_portable.py --check` fails when they are stale.
- Run the HTTP server locally: `uv run sony-alpha-viet-mcp --http --read-only --port 8765` (MCP at `/mcp`, REST at `/v1/<tool>`). Without `--http` it serves stdio for Claude Code and Gemini CLI.
- The public API deploys on Vercel from `api/index.py`.
- CI runs ruff, the test suite (186 tests) on Python 3.10 and 3.13, and checks that `portable/` is current.
- A Claude Code hook (`scripts/claude_hook.py`) blocks committing private data (PDF, XLSX, `tm.jsonl`, `LEARNING_LOG.md`, `knowledge/`) to this repo and rebuilds `portable/` after skill edits.
- Guide for AI agents reading the repo: [AGENTS.md](AGENTS.md), [llms.txt](llms.txt). Changes: [CHANGELOG.md](CHANGELOG.md).
