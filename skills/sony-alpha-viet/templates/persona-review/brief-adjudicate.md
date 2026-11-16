# Brief trọng tài: chốt các mục không đạt 3/4 phiếu

Bốn persona (S = Sony VN product specialist, E = biên tập viên ảnh, U = người dùng Alpha, P = photographer đa hãng) đã bỏ phiếu, nhưng không phương án nào đạt 3/4. Bạn chốt từng mục.

Dòng đầu mỗi mục có lý do mục bị đưa vào danh sách:
- `tie`: 2 phiếu đổi, 2 phiếu giữ.
- `split_change`: ≥ 3 phiếu muốn đổi nhưng chia cho nhiều bản.
- `winner_invalid`: bản thắng bị engine báo lỗi hoặc tràn khung.

## Luật chốt
1. `tie`: giữ bản hiện tại, **trừ khi** bản đổi sửa một lỗi khách quan:
   - sai nghĩa so với EN/CTX;
   - sai chính tả hoặc dấu;
   - sai thuật ngữ khóa;
   - thiếu hoặc thừa token;
   - sai viết hoa kiểu câu;
   - lệch với chuỗi cùng nhóm.
2. `split_change`: đa số đã cho rằng bản hiện tại có vấn đề. Chọn bản đổi tốt nhất: đúng nghĩa, đúng thuật ngữ khóa, vừa khung, tự nhiên. Chỉ giữ bản hiện tại khi mọi bản đổi đều sai hoặc tràn khung.
3. `winner_invalid`: sửa bản thắng cho hợp lệ (ngắn lại, đúng token), hoặc giữ bản hiện tại.
4. Thuật ngữ khóa và danh sách giữ tiếng Anh thắng sở thích.
5. Không tự chế cụm rút gọn (ví dụ "Nhiệt màu" cho "Nhiệt độ màu"). Không bỏ chữ phân biệt hai mục anh em (ví dụ "Rec Frame Rate" ≠ "Frame Rate").
6. Chốt về đúng OLD thì ghi `"final"` bằng OLD.

## Kết quả (JSONL, mỗi mục một dòng)
```
{"id": 123, "final": null, "note_vi": "giữ bản hiện tại: ..."}
{"id": 456, "final": "Bản chốt⏎dòng hai", "au": "B", "why_en": "English reason explaining AD -> final, max 25 words", "note_vi": "..."}
```
`final: null` = giữ bản hiện tại. Khi `final` khác null thì bắt buộc có `au` (B/F/S/G/O).
