---
title: Bộ nhớ cài đặt và Memory Recall
aliases: [Memory Recall, MR, M1–M4, Camera Set. Memory, Recall Camera Setting, Save/Load Settings, CAMPR01P.DAT]
level: nâng cao
sources: [Help Guide ILCE-7CM2 (helpguide.sony.net/ilc/2360), Help Guide ZV-E10 (helpguide.sony.net/ilc/2070), file máy A7C II firmware 2.01 và thử gọi lại trên máy (11/2026)]
menu: ["Camera Set. Memory → Bộ nhớ cài đặt", "Recall Camera Setting → Gọi lại cài đặt", "Save/Load Settings → Lưu/tải cài đặt", "Shooting Mode → Chế độ chụp"]
tags: [sony-alpha-viet/kien-thuc]
---

# Bộ nhớ cài đặt và Memory Recall

**Bộ nhớ cài đặt lưu cùng lúc một nhóm thông số của máy, gồm chế độ chụp, lấy nét, đo sáng, cân bằng trắng và Picture Profile, rồi gọi lại bằng một thao tác. Ví dụ: một bộ cho chân dung, một bộ cho phim, một bộ cho đêm.**

## Lưu bộ cài đặt ở đâu
- **Trên thân máy:** A7C II lưu 3 bộ, gọi bằng vòng chế độ 1, 2, 3.
- **Trên thẻ nhớ:** 4 bộ M1–M4. File nằm ở `PRIVATE/SONY/SETTING/<thư mục model>/CAMPR01P.DAT`…`CAMPR04P.DAT`; đuôi P là máy hệ PAL (máy bán ở Việt Nam), N là NTSC. Thư mục: ZV-E10 là `E10`, A7C II là `7CM2`.
- **Lưu/tải cài đặt** (A7C II, tab Cài đặt): lưu tới 10 bộ cài đặt toàn máy lên một thẻ; chỉ nạp được vào máy cùng model, và có thể không nạp được nếu khác phiên bản phần mềm.

## Lưu và gọi lại bộ cài đặt
- A7C II: Chụp › Chế độ chụp › Bộ nhớ cài đặt › chọn ô. Gọi bộ trên thẻ: Chụp › Chế độ chụp › Gọi lại cài đặt. Bộ lưu từ máy khác cùng model vẫn gọi được.
- A7C II: để vòng chế độ ở 1, 2 hoặc 3 rồi gọi bộ trên thẻ thì máy chạy đúng chế độ chụp (P, A, S, M), khẩu độ và tốc độ của bộ.
- Ống kính có vòng khẩu: để vòng ở A. Vòng đặt ở số F nào thì máy giữ số đó, khẩu độ trong bộ không có tác dụng.
- A7C II không lưu Tự động xem lại (Cài đặt › Tùy chọn hiển thị) vào bộ.
- ZV-E10: gọi lại bằng MENU › Cài đặt máy ảnh1 › Chế độ chụp › MR. Mục "MR Memory" là để lưu, chọn nhầm sẽ ghi đè.
- Mỗi lần lưu, máy ghi giờ lưu vào file (A7C II ghi theo giờ UTC).

## Cấu trúc file cho người viết công cụ
- ZV-E10 dùng file cố định 4.608 byte. A7C II dùng file 13.948 byte gồm 1061 bản ghi có mã; hai đời máy khác định dạng.
- Mỗi file có checksum. Trên ZV-E10, file sửa tay mà sai checksum hoặc đổi header (ngày, tên ô) thì máy báo File Error, nên header phải lấy nguyên từ file do chính máy lưu cho đúng ô.
- Khẩu độ và tốc độ lưu bằng mã APEX theo nấc 1/3, cả ZV-E10 lẫn A7C II. File A7C II còn ghi số khẩu và tốc độ đang hiện lúc lưu (ở P, A, S là số đo), nhưng máy bỏ qua số này khi gọi lại.
- Bộ M1–M4 do công cụ tạo cho A7C II, giữ header từ file máy lưu, đã gọi lại đúng trên máy thật (firmware 2.01, 11/2026).

## Mẹo khi dạy
- Lưu xong một ô, xem lại giờ của file trên máy tính: người mới hay quên bấm lưu ô cuối.
- Muốn kiểm một bộ vừa chép vào thẻ: gọi lại rồi lưu ngay vào đúng ô, không chỉnh gì ở giữa. Chỉnh tay xen vào thì không biết giá trị nào do bộ nạp.
- Chép bộ M1–M4 mới vào thẻ xong: tắt máy, tháo thẻ lắp lại rồi bật máy thì máy mới đọc (đã thấy trên ZV-E10).

## Liên quan
[[Picture Profile]] · [[Hệ menu Legacy và New-gen]] · [[Cài đặt nhanh trước buổi chụp]]
