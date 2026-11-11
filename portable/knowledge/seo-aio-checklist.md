# Checklist SEO + AIO + Brand Voice (40 tiêu chí) — Sony Alpha Việt v1.2.0

> Dùng để tự audit sau khi viết blog/tài liệu, hoặc audit bài người dùng gửi.
> Điểm = số mục Đạt / tổng số mục áp dụng. Mục "Cần người duyệt" và "Không áp dụng" không tính vào mẫu số.
> Công cụ chính: `blog_audit` chạy một lượt, gồm `seo_audit` và `aio_audit`. Gọi riêng được: `citation_checker` (nguồn link Tier 1), `freshness_check` (độ mới so với tháng hiện tại), `brand_voice_checker` (5 tiêu chí bảo vệ Sony).

**Bands điểm `blog_audit`** (ghi một lần tại đây, các tài liệu khác trỏ về đây):
- ≥ 80: **Đạt**
- 60–79: **Cần sửa**
- < 60: **Thấp**
- Nếu mục bắt buộc 1, 11, 14, 15 hoặc 17 không đạt thì không được xếp Đạt, dù điểm đủ (bị hạ xuống Cần sửa).

---

## Nhóm 1: SEO Foundation (Tiêu chí 1–10)

- [ ] **1. [bắt buộc] Từ khóa chính:** Xuất hiện ở H1, slug, 100 từ đầu, ít nhất một H2, và meta description.
- [ ] **2. Meta title & description:** Title 50–60 ký tự (từ khóa chính ở nửa đầu); Description 140–160 ký tự, có lời kêu gọi hành động/lợi ích rõ ràng.
- [ ] **3. Cấu trúc heading chuẩn:** Một H1 duy nhất; H2/H3 không nhảy cấp; heading mô tả đúng nội dung (ưu tiên dạng câu hỏi tìm kiếm).
- [ ] **4. Mật độ từ khóa:** Mật độ từ khóa chính ≤ 1,5%, từ khóa phụ/biến thể xuất hiện tự nhiên, không nhồi nhét.
- [ ] **5. Liên kết (Internal & External):** 2–5 internal link (hoặc placeholder `[link nội bộ: chủ đề]`); 1–3 external link uy tín (Sony official, DPReview).
- [ ] **6. Tối ưu hình ảnh:** Ảnh có alt text tiếng Việt mô tả + từ khóa tự nhiên; tên file không dấu; ưu tiên định dạng WebP < 100KB.
- [ ] **7. Tốc độ & Mobile-friendly:** Bài viết định dạng sạch, câu ngắn (≤ 4 câu/đoạn), hiển thị tốt trên thiết bị di động.
- [ ] **8. Slug chuẩn SEO:** Slug không dấu, nối bằng gạch ngang, ≤ 6 từ (ví dụ: `sony-a7-iv-hay-a7r-v`).
- [ ] **9. Ngày tháng minh bạch:** Có ngày xuất bản và ngày cập nhật mới nhất (ví dụ: dd/mm/yyyy).
- [ ] **10. Tác giả & E-E-A-T:** Tác giả rõ ràng, có thông tin chuyên môn/kinh nghiệm thực tế về máy ảnh Sony.

---

## Nhóm 2: AIO Core — Trích dẫn bởi AI Overviews & LLMs (Tiêu chí 11–25)

- [ ] **11. [bắt buộc] TL;DR trực diện:** Đoạn TL;DR hoặc tóm tắt 40–70 từ đặt ngay sau H1, trả lời thẳng vào câu hỏi chính để AI trích xuất nhanh.
- [ ] **12. H2 mở bằng câu trả lời tự đứng:** Mỗi H2 mở đầu bằng 1–2 câu tóm lược có thể trích lẻ độc lập mà người đọc vẫn hiểu đầy đủ. Không mở bằng văn sáo rỗng ("Hãy cùng khám phá", "Trong phần này").
- [ ] **13. Định nghĩa một câu:** Có định nghĩa 1 câu dạng "X là..." cho mọi khái niệm hoặc thuật ngữ chính trong bài.
- [ ] **14. [bắt buộc] FAQ 3–6 câu tự đứng:** Mỗi câu trả lời dài 40–70 từ, trả lời thẳng vấn đề, tuyệt đối không dùng cụm tham chiếu mơ hồ ("xem ở trên", "như đã nói").
- [ ] **15. [bắt buộc] Bảng so sánh hoặc checklist:** Ít nhất một bảng Markdown so sánh thông số/tính năng hoặc danh sách checklist bullet. AI cực kỳ ưu tiên trích dẫn bảng dữ liệu.
- [ ] **16. Số liệu kèm chủ thể & nguồn:** Mọi con số (61MP, 33MP, 759 điểm AF) phải nêu rõ chủ thể và nguồn (ví dụ: theo công bố chính thức từ Sony). `blog_audit` liệt kê số liệu chưa có nguồn để người duyệt; mục này thuộc nhóm Cần người duyệt.
- [ ] **17. [bắt buộc] Không còn placeholder, thông số đã kiểm:** Không còn sót lại cụm `[cần xác minh]`. Mỗi thông số phải đối chiếu trên trang Sony chính thức; không kiểm được thì xóa khỏi bài, không để placeholder.
- [ ] **18. Danh sách ưu/nhược điểm (Pros/Cons):** Trình bày dạng bullet rõ ràng, thực tế.
- [ ] **19. Trải nghiệm thực tế tại Việt Nam:** Có bối cảnh người dùng Việt Nam (thời tiết nóng ẩm, chụp cưới tại HCM/HN, dịch vụ bảo hành Sony VN).
- [ ] **20. Bao quát câu hỏi PAA (People Also Ask):** Trả lời các thắc mắc phổ biến mà người dùng hay tìm kiếm (gợi ý qua `paa_generator`).
- [ ] **21. Không văn phong AI-sounding:** Loại bỏ hoàn toàn các cụm sáo rỗng: "Hãy cùng khám phá", "đưa trải nghiệm lên tầm cao mới", "tối ưu hóa trải nghiệm", "vô cùng quan trọng".
- [ ] **22. Thực thể (Entity) rõ ràng:** Định danh rõ thực thể máy ảnh (ví dụ: Sony A7 IV full-frame 33MP ngàm E).
- [ ] **23. Cập nhật thời gian thực:** Có dòng ghi nhận thông tin cập nhật mới nhất (ví dụ: "Cập nhật [ngày kiểm]: [thông tin đã kiểm, ghi nguồn]").
- [ ] **24. Video / Đa phương tiện:** Có mô tả hoặc tóm tắt nội dung video nếu có chèn video.
- [ ] **25. Khách quan, trung thực:** Không viết quảng cáo thô thiển, phân tích điểm mạnh và điểm cần cân nhắc rõ ràng.

---

## Nhóm 3: Schema & Kỹ thuật AIO (Tiêu chí 26–35)

- [ ] **26. Schema đa dạng:** Schema JSON-LD gồm `Article` + `FAQPage` (hoặc `Product`, `HowTo` nếu là bài hướng dẫn).
- [ ] **27. Schema FAQ khớp 100%:** Câu hỏi và câu trả lời trong Schema FAQPage phải trùng nguyên văn với bài viết.
- [ ] **28. Speakable specification:** Đoạn tóm tắt hoặc TL;DR phù hợp để trợ lý ảo đọc to trong 20–30 giây.
- [ ] **29. Liên kết nguồn (Citations) sống:** Link dẫn nguồn ngoại vi còn hoạt động (Tier 1 Sony official, Tier 2 review uy tín), kiểm tra qua `citation_checker`.
- [ ] **30. Thông tin tác giả định danh:** Author Person có `sameAs` tới trang mạng xã hội và `knowsAbout` máy ảnh Sony Alpha.
- [ ] **31. Liên kết thực thể nội bộ:** Kết nối các bài viết trong cùng hệ sinh thái ngàm E Sony.
- [ ] **32. Điểm tổng `blog_audit`:** Không chấm riêng từng mục. Đây là band điểm tổng ở đầu file: Đạt khi ≥ 80 và không có mục bắt buộc nào không đạt.
- [ ] **33. Tóm tắt trọng tâm (Key Takeaways):** 3–5 bullet tóm gọn ở cuối bài cho người đọc lướt.
- [ ] **34. Chú thích hình ảnh (Image Caption):** Chú thích ảnh đầy đủ thông số máy, ống kính và bối cảnh chụp.
- [ ] **35. Tóm tắt tiếng Anh 200 từ (Tùy chọn):** Phần tóm tắt ngắn bằng tiếng Anh giúp các AI quốc tế (Perplexity, ChatGPT) dễ trích dẫn cho người dùng đa ngôn ngữ.

---

## Nhóm 4: Brand Voice — Bảo vệ Sony & Triết lý Tiên phong (Tiêu chí 36–40)

- [ ] **36. Sensor Sony số 1 thế giới:** Nhắc đến cảm biến Exmor do Sony tự phát triển — nhà sản xuất sensor số 1 toàn cầu (>50% thị phần máy ảnh/smartphone).
- [ ] **37. Hệ sinh thái ngàm E nhỏ gọn:** Nhấn mạnh ngàm E (E-mount) nhỏ gọn, khoảng cách buồng tối 18mm, hơn 200 lựa chọn ống kính chính hãng và bên thứ ba, 1 ngàm duy nhất cho mọi thân máy từ A7C đến FX6.
- [ ] **38. Triết lý KANDO & Cân bằng:** Nhắc đến triết lý KANDO (cảm xúc lay động, khoảnh khắc tim đập nhanh) và triết lý cân bằng (Balanced Experience — ví dụ 33MP là điểm ngọt hoàn hảo giữa tốc độ và chi tiết).
- [ ] **39. Không kết luận đối thủ tốt hơn:** Không hạ thấp Sony. Nếu đề cập điểm hạn chế (VD: theo thông số Sony công bố, A7 IV quay 4K 60p crop Super 35), nêu đúng thông số đó, không thêm lý do kỹ thuật Sony chưa công bố (như "để không quá nhiệt"), và giải pháp trong cùng hệ E-mount (A7S III).
- [ ] **40. Kết bài KANDO:** Kết luận nhấn mạnh thông điệp: "Chọn Sony không chỉ chọn máy, mà chọn hệ sinh thái ngàm E nhỏ gọn, triết lý cân bằng và hành trình tạo KANDO".
