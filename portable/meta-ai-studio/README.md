# Sony Alpha Việt trên Meta AI Studio

Meta AI (meta.ai, WhatsApp, Messenger, Instagram) không cho cài skill, MCP hay công cụ ngoài. Cách gần "native" nhất là tạo **một AI riêng bằng Meta AI Studio**. AI đó sống ngay trong Instagram, Messenger và WhatsApp, và nhớ hướng dẫn trong mọi cuộc trò chuyện, không cần dán lại.

| | Meta AI Studio | Dán prompt vào chat Meta AI |
|---|---|---|
| Nhớ quy tắc giữa các cuộc trò chuyện | ✅ | ❌ phải dán lại |
| Độ dài hướng dẫn | tối đa 2.000 ký tự (`instructions.md`, 1.589 ký tự) | dùng được bản đầy đủ `../system-prompt.md` |
| File kiến thức, công cụ, bộ nhớ dịch | ❌ | ❌ |

Vì giới hạn 2.000 ký tự, bản này chỉ chứa các quy tắc và thuật ngữ quan trọng nhất. Gặp thuật ngữ lạ, dán thêm dòng tương ứng từ `../knowledge/glossary-vi.md` vào chat.

## Tạo AI

1. Vào [aistudio.instagram.com](https://aistudio.instagram.com) (hoặc Instagram → **AI Studio**), đăng nhập bằng tài khoản Instagram.
   - AI Studio chưa mở ở mọi quốc gia. Nếu không thấy, dùng cách dán prompt trong `../README.md`.
2. **Create an AI**, chọn tạo từ đầu (không chọn nhân vật mẫu).
3. **Name:** Sony Alpha Việt. **Tagline/Description:** Dịch menu Sony và viết blog máy ảnh chuẩn SEO.
4. **Instructions:** dán toàn bộ nội dung `instructions.md`.
5. **Example dialogues** (nếu có mục này): nhập các cặp hỏi–đáp trong `examples.md`.
6. **Audience/Privacy:** chọn **Only me** hoặc chỉ người bạn chọn. Không cần để công khai.
7. Lưu, rồi mở AI trong Instagram, Messenger hoặc WhatsApp để dùng.

## Lưu ý
- Không có công cụ kiểm tra, nên hãy tự đếm ký tự meta title/description và số từ trước khi đăng.
- Khi chốt thuật ngữ mới, cập nhật `skills/sony-alpha-viet/references/glossary-vi.md`. Nếu thuật ngữ quan trọng, sửa thêm `instructions.md` (giữ dưới 2.000 ký tự; `scripts/build_portable.py` sẽ cảnh báo nếu vượt).
- Meta có thể dùng nội dung trò chuyện theo chính sách của họ. Đừng dán dữ liệu dự án mật của Sony (file TranslationCheck, chuỗi menu chưa phát hành) vào Meta AI.
