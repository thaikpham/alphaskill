# Brief vòng 1: rà độc lập bản dịch menu Sony Alpha

## Bối cảnh
Gói của bạn gồm các mục chuỗi menu, thông báo, câu trợ giúp trên máy ảnh Alpha. Mỗi mục có:
- `EN`: chuỗi gốc tiếng Anh (`EN-FULL`: dạng đầy đủ khi EN viết tắt).
- `OLD`: bản tiếng Việt hiện tại của Sony (cột AD).
- `NEW`: bản đề xuất cho cột AN. Không có `NEW` nghĩa là giữ `OLD`.
- `AU`: loại lỗi đang gán cho `OLD`:
  - B = Suggest a better translation;
  - F = By a fatal error as photographic terms;
  - S = By a spelling error;
  - G = By a grammatical error;
  - O = By the other reason;
  - `=` = không đổi.
- `CTX`: ngữ cảnh Sony mô tả (chuỗi nằm ở đâu, làm gì).
- `fit=NN%`: bản cuối chiếm bao nhiêu % bề rộng khung. `maxLines`: số dòng tối đa. `⏎` = xuống dòng.

Bản cuối = `NEW` nếu có, không thì `OLD`.

## Việc của bạn
Đọc **toàn bộ** gói, tuần tự, không lấy mẫu. Nhập vai persona được giao. Chỉ phản đối khi có vấn đề thật:
1. Sai nghĩa so với EN/CTX, hoặc dịch nhầm chức năng.
2. Sai thuật ngữ nhiếp ảnh hoặc kỹ thuật, hoặc người Việt không gọi như vậy.
3. Sai chính tả, dấu, ngữ pháp, dấu câu, viết hoa.
4. Cùng một khái niệm mà dịch khác nhau trong gói, không có lý do về khung hẹp.
5. Câu lủng củng, văn dịch máy, khó hiểu trên màn hình máy ảnh.
6. `OLD` được giữ nhưng thật ra có lỗi.
7. `NEW` không hơn `OLD`, hoặc gán sai loại lỗi `AU`.

Không phản đối vì sở thích cá nhân. Im lặng nghĩa là đồng ý. Tỷ lệ phản đối hợp lý khoảng 2–8%.

## Luật cứng (đọc `guidelines.md` trước)
- Thuật ngữ khóa và danh sách giữ tiếng Anh là quyết định đã duyệt. Không đề xuất sửa từng dòng trái với chúng. Nếu cho rằng một thuật ngữ khóa sai, ghi **một** dòng `term_dispute`.
- Bản thay thế phải:
  - giữ nguyên mọi token (`<cE660>`, `${v1}`, `%d`…);
  - có số dòng ≤ maxLines;
  - không viết tắt rụng chữ;
  - viết hoa kiểu câu;
  - dùng Unicode dựng sẵn (NFC);
  - không sót tiếng Anh, trừ các ngoại lệ đã liệt kê.
- `fit` ≥ 93%: bản thay thế không được dài hơn bản cuối.
- Lý do gửi Sony viết bằng tiếng Anh, giải thích OLD (cột AD) → bản mới. Không viết "NEW", "draft".

## Kết quả (JSONL, chỉ các mục phản đối)
```
{"id": 123, "act": "change", "new": "Bản thay thế⏎dòng hai", "au": "B", "why_en": "English reason, max 25 words", "note_vi": "Lý do ngắn, tối đa 30 từ", "conf": 3}
{"id": 456, "act": "keep_old", "why_en": "...", "note_vi": "...", "conf": 2}
{"id": 789, "act": "retype", "au": "S", "why_en": "...", "note_vi": "...", "conf": 2}
{"term_dispute": "Bracket", "current": "bù trừ", "suggest": "...", "note_vi": "..."}
```

`conf`: 3 = chắc chắn là lỗi, 2 = khá chắc, 1 = gợi ý.
