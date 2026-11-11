# Changelog

## Unreleased
- Một link cho AI: `llms-full.txt` (lõi, khoảng 90 KB) và các phần bổ sung `llms-blog.txt`, `llms-knowledge.txt`; `llms.txt` là mục lục. Sinh bằng `scripts/build_portable.py`.
- README viết lại theo quy trình một link.
- `blog_audit`: chấm checklist 40 tiêu chí một lượt, dùng chung bộ phân tích Markdown (`blog/_doc.py`) với `seo_audit`, `aio_audit`, `citation_checker`, `freshness_check`, `brand_voice_checker`. Band: ≥ 80 Đạt, 60–79 Cần sửa, < 60 Thấp; mục bắt buộc 1, 11, 14, 15, 17 không đạt thì không xếp Đạt.
- Bài mẫu `skills/sony-alpha-viet/examples/example-blog-post.md` viết lại: bỏ thông số, giá và ngày chưa kiểm chứng; đạt band Đạt của `blog_audit`.
- Đồng bộ tài liệu với code: 46 tool MCP (28 công khai); `aio_audit` chấm 13 mục AIO máy đo được.
- Lượt humanizer cho blog (chống văn AI): `writing-style-vi.md` mục "Lượt humanizer" với 18 dấu hiệu (cấu trúc "không phải…mà là", câu kết lặp, dàn dựng mở bài, gạch dài, từ AI thổi phồng); `style_lint` kiểm "dash" và "not_x_but_y"; ~15 cụm AI-sounding mới.
- `ingest_helpguide(url)`: nạp Help Guide tiếng Anh từ Sony (HTML) vào kho tài liệu; dùng `search_docs` để tra nghĩa tiếng Anh của menu item trước khi dịch. Docs tự động thêm trường `lang` ("vi" hoặc "en"); `term_report` và Obsidian bỏ qua docs tiếng Anh (không phản ánh cách dùng tiếng Việt).
- Bảo mật: `citation_checker` so khớp domain chính xác (hết nhận nhầm `notsony.com`), chặn IP nội bộ và không theo redirect; link nguồn trong HTML chỉ nhận http/https; MCP server tự bật read-only khi bind ngoài loopback; `colorlab_pack` khôi phục file cũ khi gate vitest fail.
- Trung thực: `aio_audit` bảng phải có dòng `|---|`, FAQ kiểm 40-70 từ mỗi đáp; `freshness_check` bỏ giá/firmware cứng, lấy tháng hiện tại; `paa_generator` bỏ số liệu trong gợi ý; `record_feedback` không còn tự tạo quy tắc sau 2 lần sửa, gọi `learn` để duyệt.
- CI chạy Python 3.10 và 3.13.

## 1.4.0 — 2026-11-05
- API công khai phục vụ toàn bộ kho kiến thức (`knowledge/`); TM và S-number vẫn private.
- `data_info.knowledge_count` cho phép theo dõi đồng bộ kho trên API.
- `scripts/publish.sh`: quy trình một lệnh xuất bản vault (obsidian import → push data → export public → poll API).

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
