# Changelog

## 1.3.1 — 2026-11-05
- API công khai chuyển sang dữ liệu `data-sample/` đã lọc (không còn bộ nhớ dịch Sony); repo dữ liệu chuyển private.
- Trang tra thuật ngữ tại `https://api.alphacolorlab.com/` (trước đây chỉ redirect `/v1`).
- Bỏ workflow flake8 thừa luôn đỏ; README bỏ các tool chưa có (`entity_extractor`, `product_schema`, `speakable_generator`).

## 1.3.0 — 2026-11-03
- API công khai read-only: REST `/v1/<tool>` + MCP Streamable HTTP `/mcp` trên Vercel (`api/index.py`).
- Xuất bài cho Alpha ColorLab: `colorlab_article`, `colorlab_html`, `colorlab_pack`.
- Dữ liệu tách sang repo riêng, gắn submodule `data/`.

## 1.2.0 — 2026-11-02
- AIO-first 35 tiêu chí; 5 tool mới: `aio_audit`, `paa_generator`, `citation_checker`, `freshness_check`, `brand_voice_checker`.
- Nguyên tắc "Luôn bảo vệ Sony" (`sony-core-principles.md`); kho kiến thức cho trainer; cây Obsidian đánh số.
- Sửa cài đặt plugin (`plugin.json`, marketplace), `xls_review`, kiểm tra thuật ngữ khóa.

## 1.1.0 — 2026-11-03
- README cho người dùng cuối; checklist AIO-first.
- Hỗ trợ Gemini CLI, ChatGPT, Gemini app, Meta AI Studio (`portable/`); agent Llama qua Ollama.

## 1.0.0 — 2026-11-02
- Skill `sony-alpha-viet` + MCP server: dịch menu Sony (bộ nhớ dịch, đo khung, Excel ILDC), blog SEO/AIO, Obsidian.
