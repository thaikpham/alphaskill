# Xuất bài sang Alpha ColorLab (alphacolorlab.com)

Site là nơi bài được đăng: `/blog/<id>` (kind `article`) và `/learn/<id>` (kind `knowledge`). Bài gồm đúng 10 loại khối (`tldr`, `h`, `p`, `menu`, `table`, `callout`, `compare`, `checklist`, `figure`, `embed`); nội dung không vừa loại nào thì viết thành đoạn văn. Cổng kiểm của site (`packs.test.ts`) là chuẩn cuối cùng.

Công cụ:
- `colorlab_article(bài.md)`: chuyển bài, trả `problems` theo đúng mã của site.
- `colorlab_html(bài.md)`: tạo file HTML giống trang `/blog` (nền giấy, Noto Sans nhúng sẵn, JSON-LD). Thêm `fragment=True` để lấy khối `<div class="clab">` dán vào CMS khác.
- `colorlab_pack([bài.md…], "<tên-pack>")`: ghi pack vào repo site (`colorlab_repo` trong config), chạy cổng kiểm. Cổng trượt thì tự hoàn tác. Không bao giờ chạy `push:lab`; chủ site tự chạy, bài vào dạng nháp.

## Viết Markdown cho site
```markdown
---
title: "Lấy nét bằng ngón tay cái: bỏ nửa cò, dùng AF-ON"
dek: "Câu dưới tiêu đề, tối đa 220 ký tự."
slug: "lay-net-bang-ngon-tay-cai"
read: "7 phút đọc"
topic: af            # setup color af exposure composition lens body video audio post gear firmware
level: mid           # newbie mid pro
archetype: technique # setup-guide versus technique explainer fix gear recipe
author: "Thai Pham"
updated: "02/11/2026" # ngày kiểm nguồn
related: ["product:sony-ilce-6700-bqap2"]
# trang kiến thức: kind: knowledge · section: fundamentals|sony-color|workflows · order: 3
---
# Tiêu đề

**TL;DR:**
- Ý 1 (quyết định hoặc hành động)
- Ý 2
- Ý 3

Đoạn mở đầu bắt đầu bằng định nghĩa "X là …", 40–60 từ.

## Tiêu đề mục là một câu có động từ
Đoạn đầu mục (thành dòng tóm tắt trong mục lục bên phải).

> Đời cũ: MENU → Camera Settings1 → AF w/ shutter → Off
> Đời mới: MENU → Focus → AF/MF → AF w/ Shutter → Off

> **Nếu bạn chụp RAW:** callout ghi điều kiện, không ghi "Lưu ý".

| Cột 1 | Cột 2 | Cột 3 |
|---|---|---|
| (3 đến 6 dòng) | | |

*Chú thích bảng: điều kiện đo.*

> **So sánh:** 1/30, ISO 400 | 1/125, ISO 1600
> Chú thích ảnh so sánh (nhãn là thông số, không phải "Trước/Sau").

https://www.youtube.com/watch?v=<id>

*Chú thích video.*

## Câu hỏi thường gặp
### Câu hỏi người ta thật sự tìm?
Một đoạn trả lời tự đứng được.

**Kiểm tra trước khi chụp:**
- [ ] 3 đến 6 mục kiểm được bằng mắt trên máy

## Nguồn tham khảo
- [Tên trang Help Guide](https://helpguide.sony.net/…)
```

## Luật của site (khác chế độ C thông thường)
- Bài thường: 8–16 khối, mở bằng `tldr` rồi đến `p`, **kết bằng checklist**. Vì vậy FAQ đặt trước checklist; heading "Câu hỏi thường gặp" bị bỏ, mỗi câu hỏi tính 2 khối. Bài nên có 2–3 câu hỏi, phần còn lại để ở trang kiến thức.
- Không hai khối cùng loại liền nhau, trừ `menu`. Hai đoạn liền nhau sẽ bị gộp thành một.
- Không có danh sách gạch đầu dòng thường: công cụ gộp danh sách thành một đoạn và báo lại để viết lại thành văn xuôi.
- Bảng đúng 3 cột, 3–6 dòng, có chú thích. Bảng so sánh nhiều thông số thì tách thành nhiều bảng hoặc đưa sang trang kiến thức.
- Không dùng emoji, `!`, `[cần xác minh]`, `[CẦN BỔ SUNG`. Ảnh (`figure`) tải lên sau từ trang Sửa trên site; báo cáo ghi rõ ảnh nào cần thêm ở mục nào.
- **Tên mục menu giữ đúng tiếng Anh in trên máy** (`AF w/ Shutter`, `Creative Look`) theo ADR 0004 của site. Phần giải thích viết tiếng Việt. Chuẩn này khác chế độ A và B (dùng tên Menu OSD tiếng Việt).
- Thông số máy chỉ lấy từ `src/lib/camera/constants.ts` của site, hoặc từ trang Help Guide đã đọc trong ngày (`npx tsx scripts/research/sony-source.ts <url>`). Mỗi URL phải trả 200.
- Nguyên tắc vàng vẫn áp dụng: bảo vệ Sony, không kết luận đối thủ tốt hơn.

## Quy trình
1. Viết hoặc sửa bài theo mẫu trên (Obsidian `6 Blog/`).
2. Chạy `colorlab_article`, sửa đến khi `problems` rỗng. Đọc thêm `notes`: đoạn bị gộp, danh sách bị chuyển thành đoạn, ảnh cần tải lên.
3. Chạy `colorlab_html` rồi xem bản trên điện thoại và máy tính.
4. Chạy `colorlab_pack` để ghi pack vào repo site.
5. Tạo nhánh và PR theo `.github/pull_request_template.md` của site. Gửi chủ site các lệnh sau:
   - `npm run push:lab -- --target content --pack <tên> --dry-run`
   - `npm run push:lab -- --target content --pack <tên>`
