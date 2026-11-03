# Dùng Sony Alpha Việt với Gemini, ChatGPT, Meta AI

Gói này giúp các trợ lý AI khác làm việc theo cùng quy tắc với skill trong Claude Code.

| File | Dùng làm |
|---|---|
| `system-prompt.md` | Hướng dẫn hệ thống (khoảng 5.800 ký tự, dưới giới hạn 8.000 của Custom GPT) |
| `knowledge/` | File kiến thức: glossary, quy trình menu, checklist SEO/AIO, văn phong, mẫu bài, mẫu Schema, bài mẫu |

`knowledge/` được sinh tự động từ `skills/sony-alpha-viet/`. Sau khi sửa skill, chạy lại:
```bash
uv run python scripts/build_portable.py
```

## So sánh mức hỗ trợ

| Nền tảng | Quy tắc + glossary | File kiến thức | Công cụ MCP (bộ nhớ dịch, đo độ rộng, chấm SEO tự động) |
|---|---|---|---|
| Claude Code | ✅ | ✅ | ✅ |
| Gemini CLI | ✅ | ✅ | ✅ |
| ChatGPT (Custom GPT) | ✅ | ✅ | Chỉ khi bật developer mode và có server HTTPS (xem bên dưới) |
| Gemini app (Gem) | ✅ | ✅ | ❌ |
| Meta AI (AI Studio) | ✅ bản nén 2.000 ký tự, nhớ giữa các chat | ❌ | ❌ |
| Meta AI (dán prompt) | ✅ bản đầy đủ, chỉ trong một chat | ❌ | ❌ |

Không có MCP, trợ lý vẫn dịch và viết theo quy tắc, nhưng **không** có:
- bộ nhớ hàng nghìn chuỗi đã duyệt;
- đo độ rộng chữ trên màn hình máy;
- tự học từ lần sửa;
- đọc/ghi file `.xls` của Sony;
- chấm SEO bằng máy.

Khi đó, hãy kiểm tra lại độ dài meta và số từ.

---

## Gemini CLI (đầy đủ nhất ngoài Claude Code)

Cần [uv](https://docs.astral.sh/uv/):
```bash
gemini extensions install https://github.com/thaikpham/alphaskill
```
Extension gồm skill `sony-alpha-viet` và MCP server. Để dùng dữ liệu riêng, ghi đường dẫn vào `~/.config/sony-alpha-viet/config.json` (`{"data": "…"}`), hoặc đặt `SONY_VN_DATA` trước khi chạy `gemini`.

## ChatGPT — Custom GPT

Cần gói ChatGPT có quyền tạo GPT.

1. Vào chatgpt.com → **GPTs** → **Create** → tab **Configure**.
2. **Name:** Sony Alpha Việt. **Description:** Dịch menu Sony và viết blog máy ảnh chuẩn SEO/AIO.
3. **Instructions:** dán toàn bộ `system-prompt.md`.
4. **Knowledge:** tải lên 7 file trong `knowledge/`.
5. **Capabilities:** bật Code Interpreter để GPT đếm ký tự meta và số từ chính xác. Bật Web Search nếu muốn đối chiếu thông số.
6. **Conversation starters** gợi ý:
   - Dịch các mục menu này sang tiếng Việt: …
   - Viết blog "…" với từ khóa chính "…"
   - Audit SEO AIO bài viết này

### ChatGPT + công cụ MCP (nâng cao)
ChatGPT chỉ kết nối được MCP server **từ xa qua HTTPS**, qua developer mode (tùy gói tài khoản). Cách làm:

1. Chạy server ở chế độ HTTP, chỉ đọc:
   ```bash
   uv run sony-alpha-viet-mcp --http --read-only --host 127.0.0.1 --port 8765
   ```
2. Đưa endpoint `http://127.0.0.1:8765/mcp` ra Internet qua HTTPS, ví dụ bằng Cloudflare Tunnel hoặc ngrok.
3. Trong ChatGPT: **Settings → Apps & Connectors → Advanced → Developer mode** → tạo connector với URL `https://<tên-miền>/mcp`.

> ⚠️ **Bảo mật:**
> - Server **không có xác thực**. Ai biết URL đều gọi được.
> - Luôn dùng `--read-only`. Cờ này tắt các công cụ ghi dữ liệu và đọc/ghi file trên máy.
> - Khi mở ra Internet, **không** trỏ `SONY_VN_DATA` vào bộ nhớ dịch riêng (ví dụ dữ liệu ILDC của Sony). Công cụ `search_memory` sẽ trả nội dung đó cho bất kỳ ai. Hãy dùng dữ liệu mẫu (để trống `SONY_VN_DATA`).
> - Tắt tunnel khi không dùng.

## Gemini app — Gem

1. Vào gemini.google.com → **Gems** → **New Gem**.
2. **Name:** Sony Alpha Việt.
3. **Instructions:** dán `system-prompt.md`.
4. **Knowledge:** tải lên các file trong `knowledge/`. Nếu bị giới hạn số file, ưu tiên `glossary-vi.md`, `seo-aio-checklist.md`, `writing-style-vi.md`, `blog-post-template.md`.
5. Lưu, rồi mở Gem để dùng.

## Meta AI

**Cách 1 — Meta AI Studio (khuyến nghị):** tạo một AI riêng, nhớ quy tắc trong Instagram, Messenger và WhatsApp. Xem [`meta-ai-studio/README.md`](meta-ai-studio/README.md). Phần hướng dẫn được nén còn 1.589 ký tự để vừa giới hạn 2.000.

**Cách 2 — dán prompt** (khi AI Studio chưa mở ở nước bạn):

1. Mở cuộc trò chuyện mới tại meta.ai (hoặc trong WhatsApp, Messenger, Instagram).
2. Gửi tin nhắn đầu tiên: `Trong cuộc trò chuyện này, hãy làm theo hướng dẫn sau:` rồi dán toàn bộ `system-prompt.md`.
3. Gửi yêu cầu như bình thường. Nếu cần thuật ngữ ngoài bảng tóm tắt, dán thêm phần liên quan của `knowledge/glossary-vi.md`.

Lưu ý:
- Hướng dẫn chỉ có hiệu lực trong cuộc trò chuyện đó.
- Hội thoại dài có thể làm trợ lý "quên" quy tắc. Nhắc lại khi thấy trả lời lệch chuẩn.
- Không có công cụ kiểm tra tự động, nên hãy tự đếm ký tự meta.

## Giữ các nền tảng đồng bộ

Nguồn duy nhất là `skills/sony-alpha-viet/`.
1. Khi chốt thuật ngữ mới, sửa `references/glossary-vi.md`.
2. Nếu thuật ngữ quan trọng, cập nhật thêm bảng tóm tắt trong `system-prompt.md`.
3. Chạy `scripts/build_portable.py`.
4. Tải lại file lên Custom GPT và Gem.
