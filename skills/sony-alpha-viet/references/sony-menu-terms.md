# Dịch menu Sony (chế độ A)

Công cụ: MCP server `sony-alpha-viet` (tools `mcp__sony-alpha-viet__*`) — bộ nhớ dịch ILDC Rev.3 (8.346 chuỗi đã duyệt, 698 thuật ngữ trong bộ dữ liệu mẫu, quy tắc thay thế). Nếu chạy server cũ `sony-vn-translator`, dùng `mcp__sony-vn-translator__*` thay thế. Không thấy tools → báo người dùng cài theo README plugin; không tự đoán quy tắc, chỉ dùng glossary-vi.md và ghi rõ "chưa kiểm bằng MCP".

## Quy tắc menu (tóm tắt — `mcp__sony-alpha-viet__get_guidelines()` là bản đầy đủ, mới nhất)
1. **Thuần Việt**, không trộn Anh–Việt **trừ** hai nhóm: (a) tên riêng Sony, ứng dụng, chuẩn, ký hiệu kỹ thuật (`mcp__sony-alpha-viet__get_guidelines("exceptions")`); (b) **keep_english** — thuật ngữ người dùng chốt giữ tiếng Anh vì tiếng Việt không giúp hiểu hơn: Zoom, Time Code, Preset, Firmware (`mcp__sony-alpha-viet__get_guidelines("keep_english")`). Viết hoa theo bản gốc EN.
2. **Thuật ngữ khóa thắng mọi thứ** (shutter = màn trập, Shutter Button = nút chụp, Bracket = bù trừ, Defocus = xóa phông, Tracking = theo dõi, Mechanical Shutter = màn trập cơ).
3. **Không viết tắt rụng chữ** ("ság", "vòg", "đ.ký"). Không vừa khung (BORDER/OVER): **lấy `short_candidates` từ `check_translation` (hoặc `suggest_short`)** trước khi tự nghĩ. Thứ tự ưu tiên: bản đã duyệt cùng khái niệm (vd. Anti-flicker Set. = Chống nhấp nháy) → **bỏ hẳn từ mà ngữ cảnh menu ngầm hiểu** ("Chọn", "Cài đặt", "Chụp", "Chế độ", "Chức năng") → dạng `short` → cuối cùng mới cắt âm tiết có dấu chấm và ghi "cần kiểm tra bằng SonyTool". Đừng dừng ở bản chỉ bớt một từ nếu bản gọn hơn vẫn rõ nghĩa: Anti-flicker Shoot Sel. = **Chống nhấp nháy** (không phải "Chụp chống nhấp nháy").
4. **Trước khi đề xuất dịch một thuật ngữ đang để tiếng Anh**, tự hỏi: bản Việt có giúp người dùng hiểu hơn không? Nếu thuật ngữ là tên nút/tính năng quay phim chuyên dụng mà người dùng Việt quen gọi bằng tiếng Anh (Zoom, Time Code, Preset, Firmware, LUT, Log…), **giữ nguyên** và chỉ ghi chú — không xếp vào lỗi "sót tiếng Anh".
5. Giữ nguyên `${v1}`, `<cE660>`, dấu chấm thập phân (0.3EV, f/2.8). Line Feed = Off: được ngắt dòng khác bản tiếng Anh, miễn số dòng ≤ max(cột Rows, số dòng của chuỗi tiếng Anh). Luôn dùng Unicode NFC (ký tự dựng sẵn), engine báo `not_nfc` nếu sai.
   Gợi ý rút gọn (`short_candidates`/`suggest_short`) chỉ lấy bản đã duyệt của **cùng chuỗi gốc**, bỏ động từ đầu nhãn, hoặc dạng ngắn trong glossary; vẫn phải đọc lại nghĩa trước khi dùng. Verdict `CHECK` = chính chuỗi tiếng Anh cũng vượt khung theo ước lượng → nghi dữ liệu layout, kiểm bằng SonyTool.
6. Viết hoa kiểu câu: chữ đầu, tên riêng, viết tắt.
7. Help text: khi rà bản Sony, chỉ sửa sai nghĩa và thuật ngữ, không viết lại cho hay hơn. Khi dịch mới hoặc được yêu cầu viết tự nhiên, theo mục "Help text và thông báo trên máy" trong `writing-style-vi.md`.

## Quy trình
1. **Đầu vào.** Nhận chuỗi gốc, ảnh chụp màn hình, CSV/JSON, file `*_TranslationCheck_VN.xls` hoặc đoạn trích resource. Hỏi model máy và ngôn ngữ nguồn nếu chưa rõ.
2. **Gom theo màn hình/menu.** Giữ thứ tự cây menu (tab → trang → mục → giá trị). Không dịch rời rạc khi ngữ cảnh quyết định nghĩa (ví dụ "Off", "Mode", "Area").
3. **Tra.** `mcp__sony-alpha-viet__get_guidelines()` một lần mỗi phiên → `mcp__sony-alpha-viet__prepare_batch(items)` (≤ ~60 chuỗi/lần, kèm `max_width/font_w/font_h/rows/linefeed` nếu có). Có `exact_match` → dùng nguyên văn trừ khi người dùng yêu cầu dịch lại. Để tra nghĩa tiếng Anh của một menu item trước khi dịch, dùng `mcp__sony-alpha-viet__search_docs("<item>")` (cần phải ingest help guide trước bằng `ingest_helpguide(url)`; ví dụ `ingest_helpguide("https://helpguide.sony.net/ilc/2230/v1/en/index.html")` cho α7RV).
4. **Dịch** phần còn lại, bám `terms` (ưu tiên `locked`) và bản `memory` gần giống. Nguồn tiếng Nhật: dùng cột JP trong glossary để nhận diện; nếu có bản tiếng Anh cùng model thì đối chiếu tên mục.
5. **Kiểm.** `mcp__sony-alpha-viet__check_translation(en, vi, layout…)` từng chuỗi (autofix bật) đến khi `ok`. `fit.verdict` = BORDER/OVER → rút gọn theo quy tắc 3.
6. **Xuất** bảng `STT | Nguồn (EN/JP) | Tiếng Việt | Loại UI | Ghi chú` + CSV theo `templates/menu-translation-table.csv`. Ghi chú chỉ khi có lý do (thuật ngữ mới, độ rộng, ngoại lệ, phương án thay thế).
7. **Thuật ngữ mới** → `search_docs` xem Sony Việt Nam đã dùng chữ gì (ưu tiên tài liệu đời mới) → đề xuất 2–3 phương án, khuyến nghị một; người dùng chốt → `record_term` + thêm vào glossary-vi.md.
8. **Kiểm tra chéo 4 persona (bắt buộc)** theo `persona-review.md`: Sony VN product specialist, biên tập viên ảnh, người dùng Alpha lâu năm, photographer đa hãng. Chưa qua bước này thì không giao bản cuối.
9. **Kiểm tra bằng người Việt (bắt buộc trước khi gửi Sony):** file rà soát 2 cột English | Vietnamese đã lọc trùng (`python -m sony_alpha_viet.xls.review_pairs`) → nhóm sửa → áp lại vào cả bộ file → chốt.

Loại UI: `Tiêu đề menu` · `Mục menu` · `Giá trị` · `Nút` · `Thông báo` · `Trợ giúp` · `Biểu tượng/nhãn ngắn`.

## File Sony *_VN.xls
- **Rà toàn bộ một bộ file đã dịch:** `mcp__sony-alpha-viet__xls_review(folder, out_csv)` chấm mọi dòng của mọi file trong thư mục. Bản được chấm là **AN nếu có, không thì cột VI**. Cột VI là bản cũ của Sony, quét riêng cột VI hoặc nhầm sang thư mục nguồn sẽ ra hàng nghìn lỗi giả (đã gặp). Chỉ ghi AN cho **lỗi thật**: sai nghĩa, sai thuật ngữ khóa, chính tả hay mã hóa, lệch bộ nhớ đã duyệt. Dòng BORDER/OVER/CHECK đưa vào file rà soát độ rộng (CSV, note Obsidian) kèm gợi ý; không ghi AN khi chưa xác nhận bằng SonyTool, trừ khi người dùng bảo áp luôn: khi đó AV mở đầu bằng "Width to be confirmed with SonyTool (estimated overflow)." Ghi kết quả ra thư mục mới.
  - `variant_word_choice`: cùng chuỗi gốc (bỏ qua icon/biến) mà dịch khác, và bản đa số vẫn vừa khung của dòng lệch. Đây mới là lệch thật. Bản ngắn ở khung hẹp là rút gọn hợp lệ, không báo.
  - `locked_term` chỉ là cảnh báo: thuật ngữ khóa có thể gắn một ngữ cảnh (Active = Chủ động là của SteadyShot; giá trị bật công cụ nhà phát triển là "Hoạt động"). Đọc cột Reference trước khi sửa.
  - Trước khi viết AV kiểu "Glossary X = Y", tra lại glossary (`lookup_term`). Đã gặp AV trích sai glossary để biện minh cho bản dịch trái thuật ngữ khóa (S164929).
- Đọc: `mcp__sony-alpha-viet__xls_read(path, only_flagged=True)` lấy dòng vi phạm; layout lấy từ file.
- **Không mở rồi lưu file Sony bằng LibreOffice/Excel**: lưu đè có thể cắt các dòng phụ của Sony (đã gặp: 7.094 → 2.002 dòng) và đổi `\r\n` trong tiêu đề. Nếu số dòng sheet VN giảm bất thường so với bản gốc, báo người dùng trước khi dùng file.
- Ghi: `mcp__sony-alpha-viet__xls_write(src, out, proposals)` — chỉ ghi AN (đề xuất), AU (loại lỗi), AV (lý do bằng **tiếng Anh**, Sony Nhật đọc). Luôn ghi ra file mới. Chỉ đề xuất khi thực sự khác bản hiện tại.
- **Rà lần 2 (dòng đã có AN):** `xls_write(..., overwrite=True)`; mặc định engine từ chối ghi vào ô đã có giá trị. Giữ AU cũ, nối lý do mới vào AV: `<AV cũ> | Review 2: …`. Trình tự: sao lưu thư mục output → ghi ra thư mục mới → so mọi ô khác của sheet VN phải giữ nguyên → mới chép đè vào output → `remember_translation(en, vi, tm_id=S#)` cho từng chuỗi đã sửa để bộ nhớ khớp file.
- **Áp bảng thuật ngữ đã chốt vào cả bộ file** (bảng cross-check gồm English, Vietnamese = bản đang dùng, AGREED): `mcp__sony-alpha-viet__xls_apply_agreed(folder, agreed_csv, out_folder, apply_overflow=False, width_csv)`.
  - Mỗi dòng ghép với AGREED theo English. Nếu một chuỗi English có nhiều dòng AGREED, chọn dòng có cột Vietnamese trùng bản hiện tại (AN nếu có, không thì VI).
  - Không đụng dòng giữ tiếng Anh, dòng không có trong bảng, dòng mà AN đã bằng AGREED.
  - AGREED trùng VI mà đang có AN: xóa AN/AU/AV.
  - Đề xuất mới: AN = AGREED; AU "Suggest a better translation" ("By a spelling error" nếu chỉ khác dấu hoặc hoa thường); AV là lý do cụ thể dạng `'cũ' → 'mới'`, câu viết lại nhiều thì ghi lý do chung.
  - Đã có AN khác AGREED: AN = AGREED, giữ AU, AV = `<AV cũ> | Review 2: <lý do>`.
  - Dòng AGREED ước lượng tràn khung: engine **thử xuống dòng lại trước** (`core.rebreak`, cùng chữ, ngắt dòng mới). Vừa thì ghi bản đó, AV có "Line breaks re-arranged to fit the frame". Không vừa thì mặc định bỏ qua và liệt kê trong `width_csv` để kiểm bằng SonyTool. Người dùng bảo áp luôn thì dùng `apply_overflow=True`; AV có thêm ghi chú SonyTool ở trên.
  - Bản sao Google Sheets của bộ file: làm cùng quy tắc. Ghi qua tab phụ (dữ liệu khóa theo số dòng + công thức), đọc lại so với kế hoạch, rồi mới dán giá trị vào AN/AU/AV và xóa tab phụ. Không gõ tay hàng nghìn ô.
  - File gộp `*_EN_JP_VN`: chỉ sửa cột Vietnamese, đặt bằng bản cuối của từng S# trong bộ file (AN nếu có, không thì VI) để hai nơi khớp nhau.
- **Rút gọn danh sách cần kiểm SonyTool** (dòng AV có "Width to be confirmed with SonyTool"). Làm theo lượt 26/11/2026 trên 247 dòng ILDC:
  - Xuất danh sách: File, Dòng, S#, English, AD, AN, Max Width, Font W/H, Rows, Line Feed, % ước tính, lý do; thêm cột "Kết quả SonyTool" (Vừa khung/Tràn) và "Đề xuất rút gọn".
  - **Xuống dòng lại trước khi rút chữ** (`core.rebreak`, cũng là gợi ý đầu tiên của `suggest_short`). Line Feed Off: số dòng cho phép = max(Rows, số dòng EN); giữ ngắt câu sẵn có nếu được, dòng "Khe 1/2" (Slot) đứng riêng ở cuối, tránh dòng chỉ một chữ. Line Feed On: bỏ ngắt dòng thủ công, máy tự xuống dòng. Lượt 26/11: 89/247 dòng chỉ cần xuống dòng lại.
  - Còn tràn thì rút chữ theo quy tắc 3, không viết tắt rụng chữ. Đo lại từng phương án bằng `check_fit`; ghi % ước tính và lý do cho từng đề xuất.
  - Dòng mà bản hiện tại (cả AD) cũng ước tính tràn nhiều lần: nghi Max Width sai, không đề xuất, ghi "cần xem khung thật trong SonyTool".
  - **Thuật ngữ khóa không rút dù tràn** (duyệt 26/11): "Vòng xoay của tôi 1→2→3", "Công cụ nhà phát triển" giữ nguyên, không đổi sang tiếng Anh; để SonyTool quyết định. Khung hẹp được phép: chế độ S = "Ưu tiên tốc độ" (khi "Ưu tiên màn trập" không vừa), "Tăng tốc khi giữ", "Nối USB-LAN/chia sẻ", "Điều khiển PC".
  - Áp đề xuất: AN = bản rút gọn, giữ AU; trong AV bỏ câu "Width to be confirmed with SonyTool (estimated overflow).", nối `| Review 3: Shortened to fit the frame. 'cũ' → 'mới'.` hoặc `| Review 3: Line breaks re-arranged to fit the frame; wording unchanged.`; dòng còn sát khung (93–100%) thêm "Borderline width (est. NN% of Max Width): please confirm with SonyTool."
  - Cập nhật cùng lúc: 8 file (AN/AU/AV), bảng thuật ngữ (cột AGREED, trừ dòng mà khung rộng ở file khác vẫn dùng bản đầy đủ), file gộp `*_EN_JP_VN` (theo S#), bộ nhớ dịch (`prev_vi` giữ bản Sony gốc, `note` chỉ còn cho dòng sát khung hoặc chưa rút).
- Có file gộp `*_EN_JP_VN.xls` (Sheet1: S#, JP, EN, VI) thì sửa cột VI cùng lúc: `xls.biff.apply_cells(stream, {(row0, 3): vi}, overwrite=True, sheet="Sheet1")`.
- AU hợp lệ: Suggest a better translation · By a fatal error as photographic terms · By a spelling error · By a grammatical error · By the other reason.

## Ghi nhớ & tự cải tiến
- Người dùng chốt thuật ngữ → `mcp__sony-alpha-viet__record_term(en, vi, short, note)`.
- Người dùng sửa bản dịch → `mcp__sony-alpha-viet__record_feedback(en, wrong, right, reason, always=…)`; `always=True` khi họ nói "luôn luôn / từ nay".
- Người dùng duyệt (không sửa) → `mcp__sony-alpha-viet__remember_translation(en, vi, project)`.
- Người dùng cấm một cách dịch → `mcp__sony-alpha-viet__ban_term(pattern, why)`.
- **Người dùng giữ một thuật ngữ tiếng Anh** (`record_feedback` trả về `keep_english_candidates`, hoặc họ nói "giữ tiếng Anh") → `mcp__sony-alpha-viet__keep_english(term, {"<biến thể tiếng Việt>": "{term}"}, apply=False)` để xem trước số chuỗi bộ nhớ/quy tắc/thuật ngữ bị ảnh hưởng → báo con số → `apply=True` khi người dùng đồng ý (hoặc đã nói "áp dụng cho toàn bộ"). Ghi tiếp các bản người dùng sửa nguyên văn bằng `record_feedback`.
- Người dùng rút gọn bản dịch tràn khung → `record_feedback` (engine học quy tắc rút gọn chỉ áp khi tràn).
- Cuối phiên: `mcp__sony-alpha-viet__learn()` → `mcp__sony-alpha-viet__review_memory()` (quy tắc sai → `disable_rule`) → `mcp__sony-alpha-viet__commit_memory("…")`. Báo ngắn những gì đã học.
- Không ghi nhớ khi người dùng chưa đồng ý; không ghi đè thuật ngữ khóa khi chưa được xác nhận.

## Khi chưa chắc
Đối chiếu cách gọi trong menu tiếng Việt của Canon, Nikon, Fujifilm, Panasonic Lumix (chỉ khi biết chắc), chọn từ nhiếp ảnh gia Việt hay dùng, nêu rõ là đề xuất.

## Firmware
Skill chỉ dịch text. Các dự án cộng đồng sau chỉ là **tham chiếu** về cách Sony quản lý ngôn ngữ/ứng dụng trên máy, không phải công cụ skill được tự chạy:
- PMCA-RE Reloaded — https://github.com/masterflai/pmca-re-reloaded
- Sony-PMCA-RE — https://github.com/ma1co/Sony-PMCA-RE
- OpenMemories-Tweak — https://github.com/ma1co/OpenMemories-Tweak

Bắt buộc:
- Không tự sửa, đóng gói, ký, flash firmware; không bật service mode/unlock ngôn ngữ thay người dùng.
- Chỉ trích/dịch chuỗi từ file firmware/resource khi người dùng **tự cung cấp file và xác nhận rõ**; ghi kết quả ra file mới, không ghi đè file gốc.
- Mọi câu trả lời chạm tới chủ đề này kèm cảnh báo:

> ⚠️ Can thiệp firmware hoặc dùng công cụ không chính thức (PMCA, service mode, unlock ngôn ngữ) có thể làm **mất bảo hành**, **hỏng máy (brick)**, lỗi chức năng, và có thể vi phạm điều khoản sử dụng của Sony. Chỉ làm khi bạn hiểu rõ rủi ro và tự chịu trách nhiệm.
