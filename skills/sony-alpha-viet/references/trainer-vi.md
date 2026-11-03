# Đào tạo — bộ não thứ hai của Sony Camera Trainer (chế độ D)

Kho kiến thức nằm ở `<data>/knowledge/` (dữ liệu riêng, không lên repo công khai), mirror vào vault Obsidian:
- `1 Kiến thức/` — Phơi sáng · Lấy nét và xóa phông · Màu sắc · Bố cục và góc nhìn · Kỹ thuật sáng tạo · Quy trình làm việc
- `2 Giáo án/` — khóa học, bài thực hành, cài đặt nhanh, đính chính slide

Công cụ: `search_knowledge(câu hỏi)` (không phân biệt dấu, xếp hạng theo đoạn) · `get_knowledge()` (cây) / `get_knowledge("Bù sáng")` (cả note) · `add_knowledge(note, nội dung, section)` (ghi; chỉ khi trainer đồng ý). Không có MCP: hỏi trainer nội dung note, hoặc trả lời từ kiến thức chung và ghi "chưa kiểm bằng kho kiến thức".

## Trả lời câu hỏi học viên
1. `search_knowledge` với chính câu hỏi (nguyên văn, có thể không dấu). Đọc 2–3 đoạn đầu; cần thêm thì `get_knowledge(note)`.
2. Trả lời theo khung:
   - **Một câu trả lời thẳng.**
   - **Vì sao** (1–3 ý, ví dụ dễ hình dung: vòi nước và cái cốc, núm âm lượng…).
   - **Làm trên máy Sony:** chế độ, tên mục menu theo **Menu OSD** tiếng Việt kèm tên tiếng Anh trong ngoặc (danh sách `menu:` trong thuộc tính note), giá trị gợi ý.
   - **Thử ngay:** một bài tập 1–2 phút.
   - Nguồn: tên note (`[[Bù sáng]]`).
3. Kho không có hoặc chỉ có một phần: trả lời từ kiến thức chung, ghi rõ "chưa có trong kho", đề nghị `add_knowledge`.
4. Note có ghi `[cần xác minh]`, hoặc câu hỏi về thông số/giá/tính năng theo model: không khẳng định; đối chiếu trang Sony hoặc `search_docs`.
5. Trước khi dùng số liệu từ slide, xem `Đính chính slide` (ví dụ: gấp đôi số f là **giảm** ánh sáng còn 1/4).

## Soạn giáo án
1. Hỏi (một lượt): đối tượng, thời lượng, model máy của lớp, địa điểm (trong nhà/ngoài trời, giờ trong ngày).
2. `get_knowledge()` → chọn giáo án gần nhất (`Khóa Photo Basic 3 giờ`, `Khóa Essential Photography`) → điều chỉnh, không viết lại từ đầu.
3. Khung bắt buộc: **Mục tiêu** (học viên làm được gì khi rời lớp) · **Mạch bài** có mốc phút · **Demo** (trainer làm gì trên máy) · **Thực hành** (bài nào, thiết lập chính) · **Tiêu chí đạt** · **Chuẩn bị** (thiết bị, địa điểm) · liên kết tới note kiến thức.
4. Bài thực hành lấy từ `8 bài thực hành`; mỗi bài đã có thiết lập và tiêu chí đạt.
5. Câu hỏi kiểm tra: 5–10 câu, mỗi câu một tình huống thực tế ("chụp cô dâu áo trắng ngược sáng, ảnh xám tối → chỉnh gì?") kèm đáp án và note nguồn.

## Làm giàu kho sau buổi dạy
- Câu hỏi hay của học viên → `add_knowledge("<note>", "- *Câu hỏi?* Trả lời.")` (mặc định vào mục "Câu hỏi học viên hay hỏi").
- Kiến thức mới chưa có note → tạo note mới bằng `add_knowledge("1 Kiến thức/<Nhóm>/<Tên>", nội dung, section="Hiểu nhanh")`, rồi bổ sung theo mẫu dưới.
- Trainer sửa trong Obsidian → "import Obsidian" (`obsidian_import`) → `obsidian_export()`.

## Mẫu note kiến thức
```markdown
---
title: <Tên>
aliases: [<tên tiếng Anh>, <cách gọi khác>]
level: cơ bản | nâng cao
sources: [<nguồn>]
menu: ["<EN menu> → <Menu OSD tiếng Việt>"]
tags: [sony-alpha-viet/kien-thuc]
---

# <Tên>

**<Định nghĩa một câu, trích riêng được.>**

## Hiểu nhanh
## Trên máy Sony
## Giảng thế nào
## Câu hỏi học viên hay hỏi
## Liên quan
[[Note khác]] · [[Note khác]]
```
Tên menu: tra `lookup_term` / `search_memory` (bộ nhớ dịch ILDC), không tự dịch. Tên và vị trí mục khác nhau theo model; ghi "tùy model" khi không chắc.
