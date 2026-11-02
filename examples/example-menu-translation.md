# Ví dụ: dịch chuỗi menu (chế độ A)

**Yêu cầu:** Dịch Aperture, Shutter Speed, White Balance, Focus Area, Picture Profile, Silent Shooting (EN → VI). Chưa có model → danh sách ngắn, làm luôn và ghi chú.

**Các bước đã chạy (02/11/2026):** `prepare_batch` (6 chuỗi) → 5 khớp 100% bộ nhớ ILDC Rev.3 → dịch mới 1 chuỗi → `check_translation` → ok.

| STT | English | Tiếng Việt | Loại UI | Ghi chú |
|---|---|---|---|---|
| 1 | Aperture | Khẩu độ | Mục menu | Bộ nhớ đã duyệt; thuật ngữ khóa |
| 2 | Shutter Speed | Tốc độ màn trập | Mục menu | Bộ nhớ đã duyệt; khóa. Fit 62% @ 280px |
| 3 | White Balance | Cân bằng trắng | Mục menu | Bộ nhớ đã duyệt; dạng ngắn "WB" nếu không vừa |
| 4 | Focus Area | Vùng lấy nét | Mục menu | Bộ nhớ đã duyệt |
| 5 | Picture Profile | Picture Profile | Mục menu | Tên tính năng Sony — giữ nguyên trong menu (bài viết: "Picture Profile (hồ sơ hình ảnh)") |
| 6 | Silent Shooting | Chụp im lặng | Mục menu | **Mới**, chưa có trong bộ nhớ. Đồng bộ với "Silent Mode = Chế độ im lặng". Fit 51% @ 280px. Phương án khác: "Chụp không tiếng". Khuyến nghị: Chụp im lặng |

**CSV**
```csv
stt,model,source_lang,source,vietnamese,ui_type,screen_path,max_width,fit,status,note
1,,en,Aperture,Khẩu độ,Mục menu,,310,OK,memory,locked
2,,en,Shutter Speed,Tốc độ màn trập,Mục menu,,280,OK,memory,locked
3,,en,White Balance,Cân bằng trắng,Mục menu,,254,OK,memory,short=WB
4,,en,Focus Area,Vùng lấy nét,Mục menu,,304,OK,memory,
5,,en,Picture Profile,Picture Profile,Mục menu,,280,OK,memory,Sony name kept
6,,en,Silent Shooting,Chụp im lặng,Mục menu,,280,OK,new,cần người dùng duyệt
```

**Sau khi người dùng duyệt dòng 6:** `remember_translation("Silent Shooting", "Chụp im lặng", "ILDC")`; nếu họ chốt làm thuật ngữ → `record_term` + thêm vào glossary-vi.md.

**Lưu ý model:** Tên mục khác nhau giữa đời máy (ví dụ một số model đời cũ dùng "Silent Shooting", đời mới dùng "Silent Mode"). Khi có model, đối chiếu đúng chuỗi của model đó.
