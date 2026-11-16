# Brief vòng 2: kiểm tra chéo phản đối của persona khác

Bạn là persona **chưa đọc** các mục này ở vòng 1. Phán quyết từng phản đối từ góc nhìn của bạn.

Mỗi mục có `EN`, `OLD` (cột AD), `NEW` (nếu có), `CTX`, `fit`, `maxLines`, `AU`, và các lựa chọn:
- `[0]`: giữ bản cuối hiện tại.
- `[A]`, `[B]`…: phương án của persona vòng 1, kèm người nêu, độ chắc và lý do.
- "máy kiểm": kết quả kiểm tự động.
  - `OK`/`BORDER`/`OVER` + % bề rộng. `OVER` là tràn khung, không dùng được nguyên văn.
  - "lỗi: …" là vi phạm luật cứng (token_mismatch, english_residue, abbreviation, banned, locked_term, line_count).

## Cách phán quyết (mỗi mục chọn đúng một)
- `"0"`: bản hiện tại đúng, phản đối không thuyết phục.
- `"A"`/`"B"`…: phương án đó đúng và tốt hơn bản hiện tại.
- `"C"`: bản hiện tại có vấn đề thật nhưng các phương án đều chưa ổn. Tự viết bản của bạn trong `new`.

Tiêu chí:
- đúng nghĩa theo EN/CTX;
- đúng thuật ngữ nhiếp ảnh và thuật ngữ khóa (`guidelines.md`);
- tiếng Việt tự nhiên, đúng chính tả;
- nhất quán;
- vừa khung.

Hai bản đều đúng và tự nhiên thì chọn `"0"`. Không chọn nguyên văn phương án `OVER` hoặc có "lỗi:".

Bản `new` của bạn phải:
- giữ nguyên mọi token;
- có số dòng ≤ maxLines;
- không viết tắt rụng chữ;
- viết hoa kiểu câu;
- dùng NFC;
- không dài hơn bản hiện tại khi `fit` ≥ 93%.

## Kết quả (JSONL, mỗi mục đúng một dòng)
```
{"id": 123, "pick": "A", "note_vi": "lý do ngắn, tối đa 25 từ"}
{"id": 456, "pick": "0", "note_vi": "..."}
{"id": 789, "pick": "C", "new": "Bản của bạn⏎dòng hai", "au": "B", "why_en": "English reason explaining AD -> your text, max 25 words", "note_vi": "..."}
```
