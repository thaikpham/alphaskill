# Changelog

## Unreleased
- Bảo mật: `citation_checker` so khớp domain chính xác (hết nhận nhầm `notsony.com`), chặn IP nội bộ và không theo redirect; link nguồn trong HTML chỉ nhận http/https; MCP server tự bật read-only khi bind ngoài loopback; `colorlab_pack` khôi phục file cũ khi gate vitest fail.
- Trung thực: `aio_audit` bảng phải có dòng `|---|`, FAQ kiểm 40-70 từ mỗi đáp; `freshness_check` bỏ giá/firmware cứng, lấy tháng hiện tại; `paa_generator` bỏ số liệu trong gợi ý; `record_feedback` không còn tự tạo quy tắc sau 2 lần sửa, gọi `learn` để duyệt.
- CI chạy Python 3.10 và 3.13.

## 1.3.1 — 2026-11-05
- Sửa nguyên tắc Sony: A9 III là máy full-frame mirrorless đầu tiên có global shutter; bỏ lý do crop 4K60 chưa công bố. README ghi đúng bản chất `paa_generator` (offline) và `aio_audit` (10 mục, điểm = tỉ lệ đạt).
- API công khai chuyển sang dữ liệu `data-sample/` đã lọc (không còn bộ nhớ dịch Sony); repo dữ liệu chuyển private.
- Trang tra thuật ngữ tại `https://api.alphacolorlab.com/` (trước đây chỉ redirect `/v1`).
- Bỏ workflow flake8 thừa luôn đỏ; README bỏ các tool chưa có (`entity_extractor`, `product_schema`, `speakable_generator`).

## 1.3.0 — 2026-11-03
- API công khai read-only: REST `/v1/<tool>` + MCP Streamable HTTP `/mcp` trên Vercel (`api/index.py`).
- Xuất bài cho Alpha ColorLab: `colorlab_article`, `colorlab_html`, `colorlab_pack`.
- Dữ liệu tách sang repo riêng, gắn submodule `data/`.

## 1.2.0 — 2026-11-03
- AIO-first 35 tiêu chí; 5 tool mới: `aio_audit`, `paa_generator`, `citation_checker`, `freshness_check`, `brand_voice_checker`.
- Nguyên tắc "Luôn bảo vệ Sony" (`sony-core-principles.md`); kho kiến thức cho trainer; cây Obsidian đánh số.
- Sửa cài đặt plugin (`plugin.json`, marketplace), `xls_review`, kiểm tra thuật ngữ khóa.

## 1.1.0 — 2026-11-03
- README cho người dùng cuối; checklist AIO-first.
- Hỗ trợ Gemini CLI, ChatGPT, Gemini app, Meta AI Studio (`portable/`); agent Llama qua Ollama.

## 1.0.0 — 2026-11-02
- Skill `sony-alpha-viet` + MCP server: dịch menu Sony (bộ nhớ dịch, đo khung, Excel ILDC), blog SEO/AIO, Obsidian.
