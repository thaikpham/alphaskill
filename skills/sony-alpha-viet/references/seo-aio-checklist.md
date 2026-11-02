# Checklist SEO + AIO

Dùng để tự audit sau khi viết, hoặc audit bài người dùng gửi. Xuất bảng: `# | Mục | Kết quả (Đạt / Chưa đạt / N/A) | Bằng chứng | Sửa`.
Điểm = số mục Đạt / số mục áp dụng. Mục **[bắt buộc]** chưa đạt → không coi là bài hoàn chỉnh.

## A. Từ khóa & metadata
1. **[bắt buộc]** Từ khóa chính có trong H1, slug, 100 từ đầu, ít nhất một H2, meta description.
2. Meta title 50–60 ký tự, từ khóa chính ở nửa đầu.
3. Meta description 140–160 ký tự, có lợi ích/hành động.
4. Slug không dấu, gạch nối, ≤ 6 từ (ví dụ `sony-a7-iv-hay-a7r-v`).
5. Từ khóa phụ/biến thể xuất hiện tự nhiên; không nhồi (mật độ từ khóa chính ≤ ~1,5%).

## B. Cấu trúc
6. **[bắt buộc]** TL;DR / câu trả lời trực tiếp 40–70 từ ngay sau H1.
7. Một H1; H2/H3 không nhảy cấp; heading mô tả đúng nội dung (ưu tiên dạng câu hỏi).
8. **[bắt buộc]** Ít nhất một bảng, checklist hoặc danh sách các bước.
9. Đoạn ≤ 4 câu; mỗi H2 mở bằng câu trả lời 1–2 câu trích riêng được.
10. Kết luận có hành động cụ thể (chọn gì, khi nào, làm gì tiếp).

## C. AIO / trích dẫn bởi AI
11. **[bắt buộc]** FAQ 3–6 câu hỏi thực tế, mỗi câu trả lời 40–70 từ, tự đứng được (không "như đã nói ở trên").
12. Có định nghĩa một câu cho khái niệm chính ("X là…").
13. Câu chứa số liệu nêu rõ chủ thể và đơn vị ("A7R V có cảm biến 61 MP"), không đại từ mơ hồ.
14. Có thông tin riêng/kinh nghiệm thực tế (bối cảnh Việt Nam: thời tiết, giá, dịch vụ, thể loại chụp phổ biến) — không chỉ tổng hợp thông số.

## D. E-E-A-T & nguồn
15. **[bắt buộc]** Không có thông số, giá, ngày, benchmark chưa kiểm chứng; mục chưa chắc ghi `[cần xác minh]`.
16. External link 1–3 nguồn uy tín (ưu tiên trang Sony chính thức, help guide, thông cáo).
17. Internal link 2–5 (đặt placeholder `[link nội bộ: chủ đề]` nếu chưa có URL thật).
18. Tác giả, ngày cập nhật; tuyên bố kinh nghiệm/chuyên môn nếu phù hợp.

## E. Schema & media
19. **[bắt buộc]** JSON-LD `Article` + `FAQPage` (nội dung FAQ trong Schema trùng nguyên văn với bài); `HowTo` nếu là bài hướng dẫn.
20. Ảnh có alt text tiếng Việt mô tả + từ khóa khi tự nhiên; tên file không dấu.

## F. Ngôn ngữ
21. **[bắt buộc]** Thuật ngữ theo glossary-vi.md (cột Bài viết), nhất quán toàn bài.
22. Qua lượt chống văn dịch máy và cụm "AI-sounding" trong writing-style-vi.md.
23. Không khuyến nghị y tế/tài chính/pháp lý không căn cứ.

## Cách đếm nhanh
- Ký tự meta: đếm bằng script (`python3 -c "print(len('...'))"`) thay vì ước lượng.
- Số từ tiếng Việt: đếm theo khoảng trắng (mỗi âm tiết là một "từ"), không tính Schema/meta.
