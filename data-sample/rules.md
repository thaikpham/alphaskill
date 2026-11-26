# QUY TẮC DỊCH THUẦN VIỆT - SONY ALPHA OSD MENU
## ILDC Multi Translation Check - Rev.3

### 1. NGUYÊN TẮC CƠ BẢN
- **Không để sót từ tiếng Anh** trong cột tiếng Việt, trừ ba nhóm ngoại lệ: keep_english (dòng dưới), mục 8, mục 9
- **Không mix EN-VI**: Cấm tuyệt đối dạng "Ghi hình is unavailable", "System Lỗi", "Check tệp CSDL ảnh"
- **Không viết tắt**: Không dùng CSDL, phải viết đầy đủ "dữ liệu ảnh"
- **Không giữ nguyên EN**: Bỏ hoàn toàn nhãn "(Cần review - giữ nguyên EN)"; mọi nhãn khác phải dịch, trừ ba nhóm ngoại lệ ở trên
- **Ngoại lệ giữ tiếng Anh (keep_english)**: thuật ngữ mà tiếng Việt không giúp người dùng hiểu hơn được giữ nguyên tiếng Anh, viết hoa theo bản gốc — Zoom, Time Code, Preset (người dùng duyệt 02/11/2026). Danh sách sống: `get_guidelines("keep_english")`.
- **Khi tràn khung**: chỉ ở nhãn ngắn, bỏ động từ đầu nhãn mà ngữ cảnh menu ngầm hiểu (Chọn, Cài đặt, Thiết lập; "Chụp" chỉ khi đi sau chúng) — ví dụ Anti-flicker Shoot Sel. = **Chống nhấp nháy**. Không bỏ từ trong câu trợ giúp, không bỏ "Chụp" đứng một mình ("Chụp khi không có thẻ" ≠ "Khi không có thẻ"). Chỉ dùng bản ngắn đã duyệt của **cùng chuỗi gốc**, không mượn bản dịch của chuỗi khác chỉ vì giống chữ.
- **Số dòng (Line Feed = Off)**: được ngắt dòng khác bản tiếng Anh, miễn không vượt số dòng cho phép. Số dòng cho phép = max(cột Rows, số dòng của chính chuỗi tiếng Anh) — dữ liệu Sony có chuỗi 2 dòng ("…\nSlot 1") khai Rows = 1 (học từ 8.346 chuỗi ILDC đã duyệt, 03/11/2026).
- **Mã hóa**: luôn dùng ký tự dựng sẵn (Unicode NFC). Dấu tổ hợp (NFD, ví dụ "a" + U+0303) nhìn giống hệt nhưng có thể hiển thị sai trên font máy ảnh.
- **Độ rộng ước lượng**: OK ≤ 92%; BORDER 93–100% và OVER cần SonyTool xác nhận; CHECK = chính chuỗi tiếng Anh cũng "vượt khung" theo ước lượng → nghi dữ liệu layout, không phải lỗi bản dịch.

### 2. THUẬT NGỮ MÀN TRẬP - QUAN TRỌNG NHẤT
- shutter = **màn trập** (CẤM: cửa trập, màn chập, cửa chập)
- shutter speed = **tốc độ màn trập**
- shutter type = **loại màn trập**
- shutter button = **nút chụp** (theo cách gọi Sony/Canon VN – duyệt 02/11/2026)
- shutter priority = **ưu tiên tốc độ màn trập**
- electronic shutter = **màn trập điện tử**
- mechanical shutter = **màn trập cơ** (CẤM: màn trập cơ học — duyệt 02/11/2026)
- e-Front Curtain Shut. = **màn trập trước điện tử**
- Auto Slow Shutter = **tự động làm chậm màn trập**
- Var. Shutter = **màn trập biến thiên**

### 3. LỖI HỆ THỐNG - KHÔNG MIX
- System Error = **Lỗi hệ thống** (CẤM: System Lỗi)
- Camera Error. Turn power off then on. = **Lỗi máy ảnh. Tắt nguồn và bật lại.** (CẤM: Camera Lỗi.)
- Lens Error = **Lỗi ống kính**
- Memory Card Error = **Lỗi thẻ nhớ**
- Image Database File error = **Lỗi dữ liệu ảnh** (CẤM: tệp CSDL ảnh lỗi)

### 4. DỮ LIỆU ẢNH - KHÔNG VIẾT TẮT CSDL
- Image Database File = **dữ liệu ảnh** (CẤM: tệp CSDL ảnh, CSDL)
- Check Image Database File? = **Kiểm tra dữ liệu ảnh?** (CẤM: Check tệp CSDL ảnh?)
- Checking Image Database File... = **Đang kiểm tra dữ liệu ảnh...** (CẤM: Checking tệp CSDL ảnh...)
- Updating Image Database File. Please wait... = **Đang cập nhật dữ liệu ảnh. Vui lòng chờ...**
- Preparing Image Database File. Please wait... = **Đang chuẩn bị dữ liệu ảnh. Vui lòng chờ...**
- Recovering Image Database File. Please wait... = **Đang khôi phục dữ liệu ảnh. Vui lòng chờ...**
- Image Database File is full. = **Dữ liệu ảnh đã đầy.**
- Image Database File recovery failed. = **Khôi phục dữ liệu ảnh thất bại.**
- Image Database File not ready. = **Dữ liệu ảnh chưa sẵn sàng.**

### 5. GHI HÌNH - KHÔNG MIX
- Recording is unavailable in this movie format. = **Ghi hình không khả dụng trong định dạng phim này.** (CẤM: Ghi hình is unavailable in this movie format.)
- Movie format = **định dạng phim**
- Recording = **ghi hình** (không phải Đang ghi hình khi là danh từ)
- Cannot record movie. = **Không thể quay phim.**

### 6. CÁC LỖI MIX EN-VI THƯỜNG GẶP ĐÃ FIX
- Unable to display. = **Không thể hiển thị.** (CẤM: Không thể display.)
- Unable to magnify. = **Không thể phóng đại.** (CẤM: Không thể magnify.)
- Writing to memory card. Unable to operate. = **Đang ghi vào thẻ nhớ. Không thể thao tác.** (CẤM: Writing to thẻ nhớ. Không thể operate.)
- Power insufficient. = **Nguồn không đủ.** (CẤM: Nguồn insufficient.)
- Check the connected device. = **Kiểm tra thiết bị đã kết nối.** (CẤM: Kiểm trconnected thiết bị.)
- Image protected. = **Ảnh được bảo vệ.** (CẤM: ảnh protected.)
- No space on the memory card. = **Không còn dung lượng trên thẻ nhớ.** (CẤM: Không có space on the thẻ nhớ.)
- This memory card may not be capable of recording and playing normally. = **Thẻ nhớ này có thể không có khả năng ghi và xem lại bình thường.** (CẤM: This thẻ nhớ may not be capable of Đang ghi hình)
- Displays the date in Y-M-D order. = **Hiển thị ngày theo thứ tự Năm-Tháng-Ngày.** (CẤM: Hiển thị the date in Y-M-D order.)
- Switches to power save mode when there is no operation for 1 minute. = **Chuyển sang chế độ tiết kiệm điện khi không thao tác trong 1 phút.** (CẤM: Chuyển to power save mode when...)
- This function is currently disabled. = **Chức năng này hiện đang bị tắt.** (CẤM: This function is currently disabled. này)
- Locks focus when the focus hold button is pressed. = **Khóa lấy nét khi nhấn nút giữ lấy nét.** (CẤM: Locks Lấy nét when...)
- Delete all images in this folder? = **Xóa tất cả ảnh trong thư mục này?** (CẤM: Delete all ảnh in this thư mục?)

### 7. THUẬT NGỮ KHÁC ĐÃ CHUẨN HÓA
- ND Filter = **Kính lọc ND**
- Pre-flash TTL = **TTL đèn nháy trước**
- Remote Commander = **Điều khiển từ xa**
- Fine = **Mịn**
- Extra fine = **Siêu nét**
- Flash = **Đèn flash**
- Auto HDR = **HDR tự động**
- Histogram = **Biểu đồ**
- Mass Storage = **Mass Storage** (giữ tiếng Anh, duyệt 25/11/2026)
- CTRL FOR HDMI = **Điều khiển qua HDMI**
- Backlight Portrait = **Chân dung ngược sáng**
- Touch Panel Only = **Chỉ bảng cảm ứng**
- Touch Pad Only = **Chỉ bàn di cảm ứng**
- Both Valid = **Cả hai hợp lệ**
- Rating Only = **Chỉ xếp hạng** (thống nhất Rating = Xếp hạng)
- Anti-flicker Shoot Sel. = **Chống nhấp nháy**
- Shoot Interval Priority = **Ưu tiên khoảng thời gian chụp**
- My Dial = **Vòng xoay của tôi** (duyệt 25/11/2026)
- Primary DNS Server = **Máy chủ DNS chính**
- Second DNS Server = **Máy chủ DNS phụ**
- Network = **Mạng**
- Transferring… = **Đang truyền…**
- Checking... = **Đang kiểm tra...**
- Standby... = **Chờ...**
- Blue = **Xanh dương**
- Enhances outlines in blue. = **Tăng cường viền bằng màu xanh dương.**
- Rear = **Sau**
- Side = **Bên cạnh**
- Silent Shoot. in Interval = **Chụp im lặng trong khoảng thời gian**
- Will shoot shortly. = **Sẽ chụp ngay.**
- Number of shots = **Số ảnh**
- One-push AF = **AF một lần nhấn**
- MAC Address = **Địa chỉ MAC**
- IR Remote Ctrl = **Điều khiển từ xa hồng ngoại**
- AF Illuminator Brightness = **Độ sáng đèn hỗ trợ AF**
- Commander = **Bộ chỉ huy**
- Distance Disp. Unit = **Đơn vị hiển thị khoảng cách**
- Group = **Nhóm**
- WL Ready Lamp = **Đèn sẵn sàng WL**
- Wireless Group = **Nhóm không dây**
- Ratio Control = **Điều khiển tỷ lệ**
- Continuous = **Liên tiếp**
- Human = **Người**
- Animal = **Động vật**
- Bird = **Chim**
- Title = **Tiêu đề**
- Original = **Gốc**
- Voice Memo = **Ghi chú thoại**
- Load = **Tải**
- Metering = **Đo sáng**
- Viewing = **Xem**
- Shadows = **Vùng tối**
- Fade = **Phai**
- Clarity = **Độ rõ**
- Pixel Mapping = **Ánh xạ điểm ảnh**
- Sensitive = **Nhạy**
- Higher = **Cao hơn**
- Defocus (giá trị của Xóa phông) = **Xóa phông** (KHÔNG dùng "Mất nét")
- Developer Tools = **Công cụ lập trình**

### 8. GIÁ TRỊ KỸ THUẬT ĐƯỢC GIỮ NGUYÊN (CÓ NHÃN CHUẨN)
- Tên thành phố: Hawaii, Tokyo/Seoul, Berlin/Paris, v.v. → Giữ nguyên, nhãn "Tên thành phố - giữ nguyên (chuẩn)"
- Giá trị kỹ thuật: F1.1, F2.8, x5.9, 3.2", 60 Min, 5GHz, 2.4GHz, RAW, JPEG, HEIF, OK, sRGB → Giữ nguyên, nhãn "Giá trị kỹ thuật/chuẩn - giữ nguyên (chuẩn)"
- Biến: ${v1}, ${v2}, <cE801>, <cE802>, v.v. → Giữ nguyên

### 9. QUY TẮC VIẾT HOA, CHÍNH TẢ
- Đầu câu viết hoa
- Danh từ riêng Sony giữ nguyên: SteadyShot, Eye AF, Wi-Fi, Bluetooth, HDMI, USB, FTP, DNS, RAW, JPEG, HEIF, XAVC S
- Không để sót "tệp CSDL ảnh" → phải là "dữ liệu ảnh"
- Không để sót "System Lỗi" → phải là "Lỗi hệ thống"
- Không để sót "Ghi hình is unavailable" → phải là "Ghi hình không khả dụng"

### 10. KIỂM TRA TRƯỚC KHI GIAO
- [ ] 0 dòng còn nhãn "(Cần review - giữ nguyên EN)" với VI==EN
- [ ] 0 dòng "Ghi hình is unavailable in this movie format."
- [ ] 0 dòng "System Lỗi" / "Camera Lỗi"
- [ ] 0 dòng "Check tệp CSDL ảnh?" / "Checking tệp CSDL ảnh..."
- [ ] 0 dòng "tệp CSDL ảnh" (đã thay bằng "dữ liệu ảnh")
- [ ] không trộn Anh–Việt ngoài ba nhóm ngoại lệ
- [ ] shutter = màn trập, shutter speed = tốc độ màn trập
- [ ] Tất cả "Unable to...", "Writing to...", "Power insufficient." đã dịch thuần Việt

---
**Phiên bản:** Rev.3, cập nhật 11/11/2026
**Người duyệt:** Pham Khang Thai

### 11. HELP TEXT VÀ THÔNG BÁO (duyệt 25/11/2026, bảng All Terms)
- Mô tả mục bật/tắt: **Chọn có … hay không.** Nhãn chuyển nhanh: **Bật/tắt …**; nhãn giữ nút: **… khi nhấn giữ**, giữ một lần: **… khi nhấn**
- Invalid = **Không khả dụng**; Available when… = **Dùng được khi…**; câu yêu cầu người dùng làm gì mở bằng **Hãy …**
- Enables selection of X = **Cho phép chọn X**; Assign = **gán**; Failed (trong câu) = **không thành công**
- Thẻ nhớ "higher than SDXC V60" = **từ SDXC V60 trở lên**
- Recording Media = **Thẻ ghi**; Memory Card / Rec. Media Settings = **thẻ nhớ / cài đặt thẻ nhớ**
- Preset đứng riêng giữ **Preset**; tên tính năng ghép dịch **đặt trước** (Lấy nét/Zoom đặt trước, Cân bằng trắng đặt trước)
