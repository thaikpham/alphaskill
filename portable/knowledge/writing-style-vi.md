# Văn phong tiếng Việt

Giọng: chuyên gia nhiếp ảnh nói chuyện với người chơi máy — chính xác, dễ hiểu, không màu mè. Ngôi "bạn" cho độc giả.

## Lượt chống văn dịch máy (chạy riêng sau khi dịch/viết xong)

| Dấu hiệu | Sửa |
|---|---|
| Bị động thừa: "được thực hiện bởi", "được sử dụng để" | Chủ động: "máy ảnh xử lý…", "dùng để…" |
| "Việc + động từ" mở câu: "Việc lựa chọn ống kính là…" | Bỏ "việc": "Chọn ống kính…" |
| "Một trong những… nhất", "là một" thừa | Nói thẳng |
| Chuỗi danh từ dịch xuôi: "hệ thống lấy nét tự động theo dõi thời gian thực" lặp lại | Gọi đầy đủ một lần, sau đó gọi tắt |
| "Của" dày đặc: "độ phân giải của cảm biến của máy" | "độ phân giải cảm biến" |
| Đại từ "nó" cho máy móc lặp lại | Gọi tên hoặc lược bỏ |
| Trật tự tiếng Anh: "Rất nhanh là tốc độ lấy nét" | Trật tự Việt |
| Từ Hán Việt nặng khi có từ thường: "tiến hành thao tác", "thực hiện việc chụp" | "chụp", "bấm" |
| Câu > 35 chữ | Tách đôi |

## Lượt humanizer (chống văn AI)

Chuyển thể từ humanizer (blader/humanizer, MIT). Dùng khi bài viết xong, trước style_lint.

**3 quy trình cốt lõi:**
- Không thêm/bớt dữ kiện (số, tên, ngày, nguồn).
- Đọc to và thay đổi độ dài câu.
- Giữ nguyên code, tên menu (in đậm), link.

**NGOẠI LỆ:** Câu kết "Chọn Sony không chỉ chọn máy, mà chọn hệ sinh thái E-mount…" và cụm "trải nghiệm KANDO" từ sony-core-principles.md là bắt buộc, giữ nguyên dù khớp §1/§6.

| Dấu hiệu AI-sounding | Cách sửa |
|---|---|
| "Không phải X mà là Y" hay "không chỉ… mà còn" lặp lại | Nói thẳng: "X có Y." Chỉ giữ khi nó sửa niềm tin người đọc thực sự có |
| Câu kết lặp ý đoạn trên: "Đó mới là điều quan trọng." | Xóa hoặc gộp vào đoạn trước |
| "Suy cho cùng", "điều thực sự quan trọng", "hơn hết" | Bỏ để nói thẳng thừa |
| Mở màn dàn dựng: "Hãy cùng tìm hiểu", "Nói thật nhé", "Heads up" | Xóa, nói thẳng câu chứa thông tin |
| "Đừng hiểu lầm", "Một điều cần nói", "Nhớ rằng" (cãi với người vô hình) | Xóa nếu không sửa niềm tin cụ thể |
| Ba tính từ/danh từ liền: "công nghệ, tính năng, giải pháp" | Giữ 1-2 item có thật sự khác nhau, phát triển cái tốt nhất |
| Gạch nối/dấu phẩy thừa: "máy ảnh — công cụ mạnh" | Thay bằng dấu chấm, phẩy, hay hai chấm; viết lại câu nếu cần |
| "Rào đón chồng" (các từ: "cũng", "cũng lại", "vẫn", "tuy…nhưng") | Xóa những cái thừa; viết lại cấu trúc câu |
| Từ AI hay dùng: "đóng vai trò then chốt", "minh chứng cho", "đột phá" (nghĩa bóng), "vô cùng", "tuyệt vời" | Dùng từ cụ thể hoặc thường gặp hơn trong máy ảnh: "quan trọng", "ví dụ", "thay đổi", "rất", "tốt" |
| Thổi phồng ý: "bước ngoặt lịch sử", "hành trình tuyệt vời" | Nêu sự kiện hoặc bước cụ thể; nếu đó là bước quan trọng thì giải thích tại sao |
| Ngôn ngữ bán hàng: "tuyệt đẹp", "đỉnh cao", "phải có" | Mô tả cụ thể hoặc nói "tốt cho nhu cầu X" |
| Dẫn nguồn mơ hồ: "nhiều chuyên gia cho rằng", "như mọi người biết" | Ghi tên hoặc bỏ; nếu từ Sony, viết "Sony nêu" và đính kèm link |
| In đậm trang trí (trừ tên menu): **"Quan trọng nhất"** | Xóa bold; tên menu **Vùng lấy nét** vẫn giữ |
| Câu hỏi tu từ mở/kết bài: "Bạn có bao giờ…?", "Phải không?" | Xóa hoặc viết câu tường thuật |
| Dư âm chatbot: "Hy vọng bài viết hữu ích", "Chúc bạn…", "Có gì cần hỏi không?" | Xóa; kết bài bằng lời khuyến nghị hay hành động cụ thể |
| "Bảng dưới đây so sánh" (viết về tài liệu thay vì chủ đề) | Bỏ; cho bảng vào dòng và mô tả kết quả trực tiếp |
| Định nghĩa rỗng: "X được hiểu là một khái niệm", "Y là sự kết hợp của…" | Nêu định nghĩa cụ thể hoặc ví dụ thực |

## Cụm "AI-sounding" cần tránh
"Trong thế giới nhiếp ảnh ngày nay", "Hãy cùng khám phá", "không thể phủ nhận", "đưa trải nghiệm lên một tầm cao mới", "hoàn hảo cho mọi nhu cầu", "bậc thầy", "cuộc cách mạng", "Hãy cùng tìm hiểu", "Nói thật nhé", "Đừng hiểu lầm", "Suy cho cùng", "Đó mới là điều", "đóng vai trò then chốt", "minh chứng cho", "đột phá" (khi dùng nghĩa bóng), "vô cùng", "tuyệt vời", "tuyệt đẹp", "đỉnh cao", "không thể bỏ lỡ", "Hy vọng bài viết", "Chúc bạn", "bảng dưới đây", "một trong những", mở/kết đoạn bằng câu hỏi tu từ, ba tính từ liền nhau, kết bài "Tóm lại" lặp lại thân bài.

## Thuật ngữ trong văn xuôi
- Theo cột **Bài viết/Tài liệu** trong glossary.
- Lần đầu: "lấy nét mắt (Eye AF)", "chống rung trên thân máy (IBIS)"; sau đó dùng một dạng nhất quán.
- Tên mục menu: **in đậm**, đúng như bản tiếng Việt trên máy; nếu độc giả có thể dùng máy tiếng Anh: **Vùng lấy nét** (Focus Area).
- Đường dẫn menu: **MENU → Lấy nét → AF/MF → Vùng lấy nét** (dùng "→", không dùng ">").

## Số và đơn vị
- Megapixel: "33 MP", "61 MP"; khung hình: "10 fps" hoặc "10 khung hình/giây" — chọn một, nhất quán.
- Thập phân trong văn xuôi tiếng Việt: dấu phẩy ("5,5 stop"); ký hiệu kỹ thuật giữ nguyên ("f/2.8", "0.3EV" trong tên menu).
- Hàng nghìn: dấu chấm ("1.200 từ"). Tiền: "52.990.000 đ" — chỉ khi có nguồn.
- Ngày: "02/11/2026".

## Chính tả
- Dấu thanh kiểu mới, nhất quán trong một tài liệu ("hoà/hòa" chọn "hòa").
- Viết hoa tên riêng, model; không viết hoa danh từ chung giữa câu ("Cảm Biến" → "cảm biến").
- Dấu câu sát chữ trước, cách chữ sau.
