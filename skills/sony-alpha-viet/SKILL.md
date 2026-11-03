---
name: sony-alpha-viet
description: Dịch và biên tập tiếng Việt cho tài liệu/menu Sony Alpha (nguồn Anh hoặc Nhật); viết và audit blog tiếng Việt tối ưu SEO + AIO (AI Overviews); chuẩn hóa thuật ngữ nhiếp ảnh. Dùng khi người dùng nói "dịch menu Sony", "dịch hướng dẫn/tài liệu Sony", "viết blog Sony Alpha", "SEO AIO tiếng Việt", "audit bài viết", hoặc nhắc tới OSD, ILDC, TranslationCheck, thuật ngữ máy ảnh tiếng Việt, A7/A7R/A7S/A6xxx/ZV/FX.
---

# Sony Alpha Việt

Ba chế độ, mỗi chế độ một chuẩn thuật ngữ. **Xác định chế độ trước khi làm.**

| Chế độ | Khi nào | Chuẩn thuật ngữ | Đầu ra mặc định |
|---|---|---|---|
| **A. Menu OSD** | Chuỗi menu, thông báo, help text trên máy; file `*_TranslationCheck_VN.xls` | Cột **Menu OSD** trong glossary — thuần Việt trừ ngoại lệ và danh sách keep_english; thuật ngữ khóa của MCP thắng mọi thứ | Bảng Markdown + CSV (`templates/menu-translation-table.csv`) |
| **B. Tài liệu** | Hướng dẫn sử dụng, help guide, thông cáo, PDF/DOCX/EPUB, URL | Cột **Bài viết/Tài liệu**; tên mục menu trích đúng như cột Menu OSD | Markdown giữ cấu trúc gốc; PDF nếu được yêu cầu |
| **C. Blog SEO + AIO** | Viết, biên tập, audit bài blog | Cột **Bài viết/Tài liệu** | Markdown + meta + slug + JSON-LD + bảng audit |

## Đọc trước khi làm (bắt buộc)
- Mọi chế độ: `references/glossary-vi.md`, `references/writing-style-vi.md`.
- Chế độ A: `references/sony-menu-terms.md` (quy trình + MCP + giới hạn firmware).
- Chế độ C: `templates/blog-post-template.md`, `references/seo-aio-checklist.md`, `templates/faq-schema.json`.
- Mẫu đầu ra: `examples/`.

## Hỏi trước khi tạo nội dung dài
Thiếu một trong các mục sau thì hỏi (một lượt, gộp câu hỏi), không tự đoán:
- A/B: **model máy** (A7 IV, A7R V, A6400, ZV-E1…), **ngôn ngữ nguồn** (Anh/Nhật), layout nếu cần kiểm độ rộng.
- C: **từ khóa chính**, **độc giả**, **model liên quan**, độ dài; nguồn/URL tham khảo nếu có.
Yêu cầu ngắn (dưới ~20 chuỗi menu, một đoạn văn) mà ngữ cảnh đã rõ thì làm luôn.

## Nguyên tắc dịch
1. Tự nhiên, ngắn gọn, đúng ngữ cảnh UI. Không dịch từng chữ.
2. **Luôn tra glossary**; chế độ A tra thêm MCP (`prepare_batch`) — bộ nhớ đã duyệt và thuật ngữ `locked` thắng glossary trong file này.
3. Giữ nguyên: Sony, Alpha, tên model, Zoom, Time Code, Preset, Firmware (keep_english — chỉ dịch khi tiếng Việt giúp hiểu hơn), ISO, S-Log3, S-Cinetone, XAVC S/HS/S-I, APS-C, RAW, HEIF, CFexpress, tên ứng dụng (danh sách đầy đủ ở glossary mục "Giữ nguyên").
4. Menu: bản gốc ngắn → bản dịch 2–4 từ; giữ biến `${v1}`, icon `<cE660>`, số dòng.
5. Không chắc → đưa 2–3 phương án, ghi rõ phương án khuyến nghị và lý do; người dùng chốt thì ghi nhớ (chế độ A: `record_term`).
   Trước khi đề xuất, tra **tài liệu tiếng Việt chính thức của Sony** bằng `search_docs("<cụm tiếng Việt>")`. Nêu bằng chứng dạng "Sony dùng X ở ILCE-7M5 tr.1". Tài liệu đời mới (2022 trở đi) có trọng số cao hơn đời cũ. Nếu Sony mâu thuẫn với thuật ngữ đã khóa, báo người dùng, không tự đổi.
6. Nguồn tiếng Nhật: dịch từ nghĩa, không qua tiếng Anh trung gian nếu có thể; đối chiếu tên mục với bản tiếng Anh của cùng model khi có. Cột JP trong glossary dùng để nhận diện.

## Nguyên tắc viết blog
1. Mở bài bằng **TL;DR 40–70 từ** trả lời thẳng câu hỏi chính.
2. H2/H3 là câu hỏi hoặc mô tả đúng nội dung; mỗi mục mở bằng câu trả lời 1–2 câu có thể trích riêng.
3. Có bảng so sánh, checklist/các bước, FAQ 3–6 câu, ví dụ thực tế cho người dùng Việt Nam.
4. Ghi tác giả, ngày cập nhật, nguồn uy tín (Sony chính hãng ưu tiên), Schema `Article` + `FAQPage` (+ `HowTo` nếu là hướng dẫn).
5. **Không bịa** thông số, giá, ngày phát hành, benchmark. Thông số lấy từ trí nhớ → đánh dấu `[cần xác minh]` hoặc đối chiếu trang Sony trước khi xuất. Giá Việt Nam luôn `[cần xác minh]` trừ khi người dùng cung cấp.
6. Sau khi viết: tự audit theo checklist, xuất bảng điểm + danh sách sửa.

## Quy trình
**A. Menu** → làm theo `references/sony-menu-terms.md` (mcp__sony-alpha-viet__get_guidelines → mcp__sony-alpha-viet__prepare_batch → dịch → mcp__sony-alpha-viet__check_translation → bảng/CSV → ghi nhớ khi người dùng duyệt với record_term). Rà lại cả bộ file `*_VN.xls` đã dịch: mcp__sony-alpha-viet__xls_review(thư_mục) trước, rồi mới sửa (xem mục "File Sony *_VN.xls" trong `references/sony-menu-terms.md`). MCP cũ `mcp__sony-vn-translator__*` vẫn còn dùng được nếu người dùng chạy server cũ.

**B. Tài liệu** → tra `search_docs` để dùng đúng câu chữ Sony Việt Nam đã công bố cho cùng nội dung (sạc pin, lắp thẻ, thiết lập ban đầu…) → giữ nguyên cấu trúc heading/danh sách/bảng → tên mục menu in đậm theo cột Menu OSD, lần đầu kèm tên gốc trong ngoặc nếu giúp người đọc tìm trên máy tiếng Anh → biên tập lại theo `writing-style-vi.md` (lượt chống văn dịch máy) → liệt kê thuật ngữ mới đề xuất. Nếu có MCP: dùng mcp__sony-alpha-viet__lookup_prose_term để tra thuật ngữ bài viết.

**C. Blog** →
1. Brief: search intent, từ khóa chính/phụ, câu hỏi kiểu People Also Ask, outline H2/H3, internal/external link dự kiến. Trình outline nếu bài > 1.000 từ và người dùng chưa duyệt hướng.
2. Viết theo `templates/blog-post-template.md`.
3. Tối ưu AIO: TL;DR, định nghĩa 1 câu, bảng, đoạn trả lời 50–70 từ, FAQ. Dùng mcp__sony-alpha-viet__lookup_prose_term(từ) để xác minh thuật ngữ.
4. Biên tập tiếng Việt (lượt riêng, theo `writing-style-vi.md`). Nếu có MCP: mcp__sony-alpha-viet__style_lint(bài) để kiểm tra cụm AI-sounding, bị động, độ dài câu.
5. Audit theo `references/seo-aio-checklist.md` → bảng Đạt/Chưa đạt + sửa cụ thể. Nếu có MCP: mcp__sony-alpha-viet__seo_audit(bài, từ_khóa_chính) tự động kiểm tra 21 mục máy được. Sửa luôn những gì tự sửa được, liệt kê phần cần người dùng (link nội bộ thật, ảnh, giá).
6. Sinh JSON-LD schema: mcp__sony-alpha-viet__faq_schema(bài) hoặc dùng `templates/faq-schema.json` làm mẫu.

## Obsidian (khi người dùng đã cấu hình vault)
Vault đặt trong `~/.config/sony-alpha-viet/config.json` (`"vault"`, `"vault_folder"`). Mọi thứ nằm trong `<vault>/<vault_folder>/`. Không có vault thì bỏ qua mục này.
- **Blog (chế độ C):** lưu bản nháp vào `Blog/<slug>.md`, frontmatter theo mẫu (Obsidian đọc thành Properties). Viết xong gọi `obsidian_audit_note("Blog/<slug>.md")`: công cụ ghi note `<slug> — SEO audit` và thuộc tính `seo_score`/`seo_complete` vào bản nháp. Sửa theo báo cáo rồi chấm lại.
- **Thuật ngữ:** người dùng sửa note trong `Thuật ngữ/` hoặc tạo note mới (thuộc tính `en`, `vi`, tùy chọn `short`, `locked`, `note`). Khi họ nói "import thuật ngữ từ Obsidian": gọi `obsidian_import()` → trình bảng thay đổi → chỉ `obsidian_import(apply=True)` khi họ đồng ý.
- **Sau phiên dịch có thay đổi bộ nhớ** (record_term, keep_english, learn…): gọi `obsidian_export()` để vault cập nhật. Note người dùng đang sửa dở không bị ghi đè; báo lại các note trong `skipped_pending_edits`.
- **Tài liệu Sony:** người dùng đưa thư mục PDF/DOCX của Sony → `ingest_docs(folder)` (tự chuyển font VNI, bỏ file trùng) → `obsidian_export()` tạo `Tài liệu Sony/` gồm mỗi tài liệu một note và note `Đối chiếu thuật ngữ với Sony` (lấy từ `docs_term_report()`). Tài liệu chỉ lưu trong dữ liệu riêng và vault, không đưa lên repo.
- **Rà soát nhất quán:** `consistency_report()` (hoặc note `Rà soát nhất quán`) liệt kê chuỗi có nhiều bản dịch, kèm độ rộng khung. Bản ngắn ở khung hẹp thường là rút gọn hợp lệ, đừng tự "sửa". Áp dụng lựa chọn của người dùng bằng `remember_translation(..., tm_id=S#)`.

## Firmware — giới hạn cứng
Skill **chỉ dịch và chuẩn hóa text**. Không tự sửa, đóng gói, flash firmware hay vào service mode. Chỉ làm việc với file firmware/resource khi người dùng **tự cung cấp file và xác nhận rõ ràng**, và vẫn chỉ ở mức trích/dịch chuỗi. Mọi câu trả lời liên quan đến firmware/PMCA/unlock ngôn ngữ phải kèm cảnh báo rủi ro (mất bảo hành, hỏng máy, vi phạm điều khoản). Chi tiết: `references/sony-menu-terms.md` mục "Firmware".

## Thuật ngữ mới
Đề xuất dạng: `EN/JP | Menu OSD | Bài viết | Lý do chọn`. Người dùng chốt → thêm vào `references/glossary-vi.md` (và `record_term` nếu là thuật ngữ menu). Không tự sửa thuật ngữ đã khóa.
