# Kiểm tra chéo 4 persona (chế độ A, bắt buộc)

Mọi bản dịch menu (chế độ A) phải qua bước này trước khi giao cho người dùng hoặc gửi Sony. Bản dịch từ bộ nhớ hay do AI viết đều phải qua. Không được bỏ bước vì thiếu thời gian. Nếu không chạy được (không có sub-agent, hết hạn mức…), báo người dùng là **chưa kiểm tra chéo**; không giao bản dịch như bản cuối.

Áp dụng cho:
- file `*_TranslationCheck_VN.xls` (cột AN/AU/AV);
- file gộp `*_EN_JP.xls` (cột Vietnamese);
- mọi lô chuỗi menu.

## Bốn persona

| Mã | Persona | Góc nhìn khi rà |
|---|---|---|
| **S** | Nhân viên Sony Việt Nam có kinh nghiệm chụp ảnh, đang làm product specialist ở phòng Digital Imaging | Thuật ngữ và tên tính năng đúng như Sony Việt Nam dùng trong hướng dẫn sử dụng, website, đào tạo đại lý; tên tính năng nhất quán giữa mục menu, giá trị và câu trợ giúp; không dịch sai chức năng; giọng văn chuẩn của hãng |
| **E** | Biên tập viên media ngành ảnh kỳ cựu | Chính tả, dấu, ngữ pháp, dấu câu, viết hoa kiểu câu; câu gọn, tự nhiên, không mang văn dịch máy; các thông báo cùng loại diễn đạt nhất quán |
| **U** | Người dùng máy ảnh Sony Alpha lâu năm, am hiểu khái niệm chụp ảnh | Nhìn nhãn trên màn hình có hiểu ngay và tìm đúng mục không; cộng đồng Alpha Việt Nam thật sự gọi thế nào; nhãn ngắn dễ quét mắt; thông báo lỗi có nói phải làm gì |
| **P** | Photographer hiểu kỹ thuật, đã dùng nhiều hãng máy | Độ chính xác của khái niệm (phơi sáng, đo sáng, lấy nét, màu, video, âm thanh, mạng, lưu trữ); đối chiếu cách các hãng khác gọi cùng tính năng; phát hiện chỗ nhầm giữa hai khái niệm gần nhau |

Mỗi persona là một **sub-agent riêng**, nhận brief trong `templates/persona-review/`. Persona không được gọi công cụ ghi bộ nhớ (`record_*`, `remember_translation`, `learn`, `commit_memory`, `keep_english`, `ban_term`, `xls_write`).

## Quy trình

### 0. Chuẩn bị (orchestrator)
1. Gộp trùng: các dòng có cùng EN và cùng bản dịch (đã che token `<cE…>`, `${v…}` thành ◆) gộp thành một **mục**. Mỗi mục giữ danh sách dòng gốc `[file, row, S#]`.
2. Ghi kèm mỗi mục:
   - `fit` (% bề rộng khung, theo `check_fit`), `maxLines`;
   - loại lỗi AU dự kiến;
   - EN-FULL nếu EN bị viết tắt;
   - ngữ cảnh (cột Reference).
3. Xuất `guidelines.md` từ `get_guidelines()`: luật, thuật ngữ khóa, keep_english, ngoại lệ. Persona đọc file này, không gọi MCP.
4. Chia gói ≤ ~55.000 ký tự, mỗi gói ≤ ~800 dòng. Sub-agent đọc quá ~60k token sẽ bị nén ngữ cảnh và phán quyết từ trí nhớ (đã gặp).

### 1. Vòng 1: hai persona rà độc lập mỗi gói
- Xoay cặp theo gói để mỗi persona gặp đủ ba persona còn lại: SE, UP, SU, EP, SP, EU, rồi lặp lại.
- Persona đọc **toàn bộ** gói, chỉ ghi các mục phản đối, theo schema trong `brief-r1.md`:
  - `change`: đổi thành bản khác;
  - `keep_old`: đề xuất không hơn bản Sony, nên bỏ đề xuất;
  - `retype`: đổi loại lỗi AU;
  - `term_dispute`: cho rằng một thuật ngữ khóa sai.
- Im lặng nghĩa là đồng ý. Tỷ lệ phản đối hợp lý khoảng 2–8%.
- Chạy song song, tối đa ~20 agent một lúc.
- Agent báo "phán quyết từ ghi chú tóm tắt" hoặc bị nén ngữ cảnh: cắt phần kết quả chưa chắc, chia nhỏ gói và chạy lại phần đó.

### 2. Gộp phản đối và kiểm bằng engine
- Chạy `check_translation` / `core.audit` cho từng phương án trên **mọi** layout của mục. Ghi kết quả: `OK/BORDER/CHECK/OVER` và lỗi cứng (token_mismatch, english_residue, abbreviation, banned, locked_term, line_count).
- Phương án bị OVER hoặc có lỗi cứng thì không được chọn nguyên văn.

### 3. Vòng 2: hai persona còn lại bỏ phiếu
- Mỗi mục bị phản đối được giao cho **hai persona chưa đọc nó**.
- Mỗi persona chọn một phiếu (schema trong `brief-r2.md`):
  - `"0"`: giữ bản hiện tại;
  - `"A"`/`"B"`: chọn một phương án của vòng 1;
  - `"C"`: tự viết bản mới.
- Phản đối chỉ đổi loại lỗi AU (`retype`) không đưa vào bỏ phiếu. Orchestrator xử lý theo luật AU ở bước 5.

### 4. Kiểm phiếu (4 phiếu mỗi mục)
- Người rà vòng 1 không phản đối = 1 phiếu giữ. Người phản đối = 1 phiếu cho bản họ đề xuất.
- Một bản được **≥ 3/4 phiếu** và engine hợp lệ: đổi.
- **≥ 3 phiếu giữ**, hoặc 2 phiếu giữ và ≤ 1 phiếu cho một bản đổi: giữ.
- Các trường hợp còn lại giao **trọng tài**, theo `brief-adjudicate.md`:
  - `tie` (2 giữ, 2 đổi): giữ, trừ khi bản đổi sửa một lỗi khách quan;
  - `split_change` (≥ 3 phiếu muốn đổi nhưng chia cho nhiều bản): chọn bản đổi tốt nhất;
  - `winner_invalid` (bản thắng bị engine báo lỗi): sửa cho hợp lệ hoặc giữ.
- **Luôn thắng phiếu persona:**
  - thuật ngữ khóa;
  - bản `user-approved` trong bộ nhớ. Bản persona khác bản đã duyệt thì đưa vào danh sách chờ người dùng, không tự ghi đè.
- `term_dispute`: không áp dụng. Gom lại, hỏi người dùng một lượt.
- Orchestrator rà lại kết quả cuối: không chấp nhận cụm rút gọn tự chế (ví dụ "Nhiệt màu"). Cũng không chấp nhận bản thắng làm lệch nhất quán với các nhãn anh em, như bỏ "ghi" khỏi "Rec Frame Rate" khiến nó trùng với "Frame Rate".

### 5. Luật AU khi chỉ đổi loại lỗi
- Chỉ sửa viết hoa hoặc xuống dòng: **B**.
- Viết tắt rụng chữ: **B**.
- Dính chữ hoặc sai chính tả thật ("Ko", "micro" → "micrô", "ảnhtĩnh"): **S**.
- Sai bản chất thuật ngữ nhiếp ảnh (tỷ lệ khung hình ≠ tốc độ khung hình, "chụp Log" cho phim, "cửa trập"): **F**.
- Câu đúng ngữ pháp nhưng lủng củng: **B**, không phải G.
- Chỉ dùng đúng 5 chuỗi AU của Sony.

### 6. Viết AV (lý do gửi Sony Nhật)
- Viết tiếng Anh, 8–30 từ, giải thích vì sao bản hiện tại sai và bản đề xuất sửa gì.
- Dùng tên cột của Sony: **AD** = bản hiện tại, **AN** = đề xuất. Tham chiếu chuỗi khác bằng **S#**.
- **Không bao giờ** viết các nhãn nội bộ: OLD, NEW, FINAL, CUR, draft, persona, reviewer, "item 1234".
- Mục đổi do persona hoặc trọng tài thì giao sub-agent viết lại AV theo `brief-av.md`. Ghi chú của reviewer nói về bản nháp, không dùng làm AV.
- Quét tự động trước khi ghi file: AV không chứa `\b(OLD|NEW|FINAL|CUR|item \d+)\b`.

### 7. Áp ngược và kiểm chứng
1. Áp mỗi mục về từng dòng gốc, **trả lại token riêng của dòng**. Các dòng gộp chung có thể khác icon (`<cE562>` / `<cE585>`). Quên bước này đã sinh 295 dòng sai token.
2. Ghi file bằng `xls_write` / `sonyxls.write_proposals(..., overwrite=False)` ra **file mới**. So sánh: mọi ô khác của sheet phải giữ nguyên, số dòng không đổi.
3. Chạy `xls_review` trên thư mục kết quả và so với lần chạy trước: không được có lỗi mới. Sau khi sửa các nhãn anh em, kiểm `variant_word_choice`.

### 8. Kiểm tra bằng người Việt (bắt buộc trước khi gửi Sony)
1. Xuất file rà soát 2 cột **English | Vietnamese**, lọc trùng trên cả bộ file (cả file `*_EN_JP`):

   ```bash
   python -m sony_alpha_viet.xls.review_pairs <thư mục *_VN.xls> <out.xlsx> <mapping.json>
   ```

   - Tab "Cần dịch": các cặp có bản tiếng Việt khác tiếng Anh.
   - Tab "Giữ nguyên tiếng Anh": các cặp mà bản dịch trùng nguyên văn tiếng Anh.
   - Bản tiếng Việt lấy AN nếu có, không thì AD.
   - `mapping.json` lưu dòng nào ứng với cặp nào. Giữ file này để áp ngược.
2. Giao file cho nhóm. Nếu nhóm làm việc trên Drive, tải lên dạng **Google Sheets gốc**. Nhắc nhóm:
   - chỉ sửa cột Vietnamese;
   - giữ token và chỗ xuống dòng;
   - được lọc, sắp xếp, nhưng không xóa dòng.
3. Nhận lại file đã sửa:
   - Khớp theo English. Một EN có nhiều bản dịch thì khớp bản cũ nguyên văn để biết dòng nào đã đổi.
   - Áp bản sửa cho mọi dòng của cặp.
   - Chạy engine check. Viết AV mới cho các dòng đổi.
   - Ghi lại cả bộ file theo bước 7.
4. Người dùng duyệt thì cập nhật bộ nhớ (`remember_translation(..., tm_id=S#)` hoặc cập nhật hàng loạt TM kèm trạng thái mới) và commit repo dữ liệu. Sau đó mới chốt gửi Sony.

### 9. Báo cáo cho người dùng
- Số liệu từng vòng: số mục phản đối; số mục đổi, giữ, giao trọng tài.
- Danh sách chờ người dùng quyết:
  - tranh chấp thuật ngữ;
  - bản persona trái với bản `user-approved`;
  - chuỗi tràn khung cần kiểm bằng SonyTool;
  - đề nghị đổi AU hàng loạt (ví dụ "cửa trập" sang F).

## Bẫy đã gặp
- **Google Sheets:**
  - Connector không sửa được file Office.
  - Sửa tại chỗ thì dùng `findReplace` giới hạn đúng cột, `repeatCell` cho khối liền nhau.
  - Nhiều ô rải rác thì dùng một sheet tạm rồi `copyPaste PASTE_VALUES`.
  - **Không để agent gõ tay mảng dài có `null`** cho `update_values`. Agent đếm sai sẽ ghi lệch ô (đã gặp ở 2 file).
- **Không đặt tên script trùng thư viện chuẩn** (ví dụ `inspect.py`): Python sẽ nạp nhầm script đó thay cho thư viện.
- Thư mục làm việc của một dự án (các gói, phiếu, quyết định, mapping) có chuỗi của Sony: lưu trong repo dữ liệu private (`alphaskill-data/projects/<dự án>/`), **không** đưa vào repo code.
