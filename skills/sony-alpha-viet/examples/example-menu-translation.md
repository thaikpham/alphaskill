# Ví dụ: dịch chuỗi menu (chế độ A)

**Yêu cầu:** Dịch 20 chuỗi menu sau (EN → VI). Chưa có model → làm luôn và ghi chú.

**Quy trình:** `get_guidelines` → `prepare_batch` → dịch → `check_translation` từng chuỗi → bảng + CSV. Không có tool: tra `references/glossary-vi.md` và `data-sample/glossary.json`, ghi cột Khung là "chưa đo".

| STT | English | Tiếng Việt | Loại UI | Khung | Ghi chú |
|---|---|---|---|---|---|
| 1 | Aperture | Khẩu độ | Mục menu | — | Khóa |
| 2 | Shutter Speed | Tốc độ màn trập | Mục menu | — | Khóa |
| 3 | White Balance | Cân bằng trắng | Mục menu | — | Dạng ngắn "WB" nếu không vừa |
| 4 | Focus Area | Vùng lấy nét | Mục menu | — | |
| 5 | Picture Profile | Picture Profile | Mục menu | — | Tên tính năng Sony, giữ nguyên trong menu |
| 6 | Silent Shooting | Chụp im lặng | Mục menu | — | **Mới**, chưa có trong glossary. Cần người dùng duyệt |
| 7 | Exposure Comp. | Bù sáng | Mục menu | — | Khóa |
| 8 | Metering Mode | Chế độ đo sáng | Mục menu | — | |
| 9 | Shutter Type | Loại màn trập | Mục menu | — | |
| 10 | Mechanical Shutter | Màn trập cơ | Mục menu | — | Khóa. Cấm "màn trập cơ học" |
| 11 | Flash Mode | Chế độ flash | Mục menu | — | |
| 12 | Flash Comp. | Bù flash | Mục menu | — | |
| 13 | Red Eye Reduction | Giảm mắt đỏ | Mục menu | — | |
| 14 | Movie Recording | Quay phim | Mục menu | — | |
| 15 | Frame Rate | Tốc độ khung hình | Mục menu | — | Khóa |
| 16 | Log Shooting | Quay Log | Mục menu | — | |
| 17 | Subject Recognition | Nhận dạng chủ thể | Mục menu | — | Không dùng "nhận diện" |
| 18 | Airplane Mode | Chế độ máy bay | Mục menu | — | |
| 19 | Wind Noise Reduction | Giảm tiếng gió | Mục menu | — | |
| 20 | Time Code | Time Code | Mục menu | — | Giữ tiếng Anh (keep_english, khóa) |

Cột Khung để "—": đo độ rộng bằng `check_translation` (ước lượng Liberation Sans, 92% là an toàn), cần SonyTool xác nhận.

## Khung hẹp: rút gọn theo cột "Ngắn" của bảng thuật ngữ

Không tự cắt chữ, không bỏ dấu. Dùng dạng ngắn đã duyệt; nếu vẫn tràn thì báo người dùng.

| English | Dạng đầy đủ | Dạng ngắn (khung hẹp) | Ghi chú |
|---|---|---|---|
| Aperture Priority | Ưu tiên khẩu độ | Ưu tiên khẩu | |
| Face/Eye Priority | Ưu tiên khuôn mặt/mắt | Ưu tiên mặt/mắt | |
| Peaking Display | Viền hỗ trợ lấy nét | Viền lấy nét | Khóa |
| Subject Recognition | Nhận dạng chủ thể | Nhận dạng | Chỉ khi ngữ cảnh màn hình đã rõ là chủ thể |

## Nguồn tiếng Nhật

Tra theo cột JP của `references/glossary-vi.md`; kết quả phải trùng với bản dịch từ tiếng Anh của cùng mục.

| 日本語 | English tương ứng | Tiếng Việt |
|---|---|---|
| フォーカスモード | Focus Mode | Chế độ lấy nét |
| フォーカスエリア | Focus Area | Vùng lấy nét |

**CSV** (20 chuỗi chính)
```csv
stt,model,source_lang,source,vietnamese,ui_type,screen_path,max_width,fit,status,note
1,,en,Aperture,Khẩu độ,Mục menu,,,,glossary,locked
2,,en,Shutter Speed,Tốc độ màn trập,Mục menu,,,,glossary,locked
3,,en,White Balance,Cân bằng trắng,Mục menu,,,,glossary,short=WB
4,,en,Focus Area,Vùng lấy nét,Mục menu,,,,glossary,
5,,en,Picture Profile,Picture Profile,Mục menu,,,,glossary,Sony name kept
6,,en,Silent Shooting,Chụp im lặng,Mục menu,,,,new,cần người dùng duyệt
7,,en,Exposure Comp.,Bù sáng,Mục menu,,,,glossary,locked
8,,en,Metering Mode,Chế độ đo sáng,Mục menu,,,,glossary,
9,,en,Shutter Type,Loại màn trập,Mục menu,,,,glossary,
10,,en,Mechanical Shutter,Màn trập cơ,Mục menu,,,,glossary,locked
11,,en,Flash Mode,Chế độ flash,Mục menu,,,,glossary,
12,,en,Flash Comp.,Bù flash,Mục menu,,,,glossary,
13,,en,Red Eye Reduction,Giảm mắt đỏ,Mục menu,,,,glossary,
14,,en,Movie Recording,Quay phim,Mục menu,,,,glossary,
15,,en,Frame Rate,Tốc độ khung hình,Mục menu,,,,glossary,locked
16,,en,Log Shooting,Quay Log,Mục menu,,,,glossary,
17,,en,Subject Recognition,Nhận dạng chủ thể,Mục menu,,,,glossary,
18,,en,Airplane Mode,Chế độ máy bay,Mục menu,,,,glossary,
19,,en,Wind Noise Reduction,Giảm tiếng gió,Mục menu,,,,glossary,
20,,en,Time Code,Time Code,Mục menu,,,,glossary,keep_english locked
```

**Sau khi người dùng duyệt dòng 6:** `remember_translation("Silent Shooting", "Chụp im lặng", "<mã project>")`; nếu họ chốt làm thuật ngữ → `record_term` + thêm vào `glossary-vi.md`.

**Lưu ý model:** Khi có model cụ thể, đối chiếu đúng chuỗi trên màn hình của model đó trước khi chốt.
