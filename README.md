# Sony Alpha Việt — skill + MCP cho Claude Code

Bộ công cụ cho người làm nội dung tiếng Việt về máy ảnh Sony Alpha. Có ba việc chính:

1. **Dịch menu máy ảnh (OSD)** từ tiếng Anh hoặc tiếng Nhật sang tiếng Việt. Thuật ngữ được thống nhất, bản dịch được kiểm tra có vừa khung màn hình không, và bộ công cụ ghi nhớ từng lần bạn sửa.
2. **Dịch tài liệu**: hướng dẫn sử dụng, help guide, thông cáo báo chí. Văn phong tự nhiên, không đọc như dịch máy.
3. **Viết và chấm bài blog** tiếng Việt chuẩn SEO (Google) và AIO (AI Overviews, ChatGPT, Perplexity). Có TL;DR, bảng so sánh, FAQ, Schema JSON-LD và bảng tự chấm điểm.

Repo này là một **Claude Code plugin** gồm hai phần:

| Phần | Vai trò |
|---|---|
| **Skill** `sony-alpha-viet` | "Sổ tay nghề" cho Claude: khi nào dùng chế độ nào, quy tắc dịch, glossary, văn phong, mẫu bài, checklist SEO/AIO, ví dụ đầu ra. |
| **MCP server** `sony-alpha-viet` | Bộ công cụ chạy thật: tra bộ nhớ dịch, kiểm tra và tự sửa bản dịch, đo độ rộng chữ trên màn hình, ghi nhớ và tự học, đọc/ghi file Sony `*_TranslationCheck_VN.xls`, chấm SEO/AIO, kiểm văn phong, sinh Schema. |

Skill cho Claude biết **phải làm gì và theo chuẩn nào**. MCP **làm và kiểm** những việc máy làm chính xác hơn người: đếm ký tự, đo độ rộng, so khớp hàng nghìn chuỗi đã duyệt.

---

## Mục lục
- [Ứng dụng thực tế](#ứng-dụng-thực-tế)
- [Cài đặt](#cài-đặt)
- [Dùng với Gemini, ChatGPT, Meta AI](#dùng-với-gemini-chatgpt-meta-ai)
- [Dữ liệu và bộ nhớ dịch](#dữ-liệu-và-bộ-nhớ-dịch)
- [Cách dùng](#cách-dùng)
  - [Chế độ A: dịch menu máy ảnh](#chế-độ-a-dịch-menu-máy-ảnh)
  - [Chế độ B: dịch tài liệu](#chế-độ-b-dịch-tài-liệu)
  - [Chế độ C: viết và chấm blog SEO + AIO](#chế-độ-c-viết-và-chấm-blog-seo--aio)
- [Quy tắc thuật ngữ](#quy-tắc-thuật-ngữ)
- [Tự học từ lần sửa của bạn](#tự-học-từ-lần-sửa-của-bạn)
- [Danh sách công cụ MCP](#danh-sách-công-cụ-mcp)
- [Cấu trúc repo](#cấu-trúc-repo)
- [Giới hạn và an toàn](#giới-hạn-và-an-toàn)
- [Câu hỏi thường gặp](#câu-hỏi-thường-gặp)
- [Phát triển](#phát-triển)

---

## Ứng dụng thực tế

| Bạn là | Dùng để |
|---|---|
| **Người dịch / rà soát menu cho Sony** (file ILDC TranslationCheck) | Đọc file `.xls`, lọc các dòng vi phạm quy tắc, đề xuất bản sửa vừa khung, ghi cột AN/AU/AV ra **file mới** (không đụng file gốc), kèm lý do bằng tiếng Anh cho phía Sony Nhật. |
| **Blogger / reviewer máy ảnh** | Viết bài so sánh, hướng dẫn cài đặt, review có TL;DR, bảng, FAQ, Schema. Tự chấm theo 23 tiêu chí SEO/AIO trước khi đăng. |
| **Người làm YouTube / mạng xã hội** | Dịch kịch bản, chú thích, tên mục menu cho đúng cách gọi trên máy tiếng Việt. |
| **Cửa hàng, nhà phân phối** | Dịch tài liệu sản phẩm, trang FAQ, hướng dẫn nhanh với thuật ngữ thống nhất trên mọi kênh. |
| **Người dùng muốn hiểu menu máy** | Tra một mục menu (EN/JP) ra tên tiếng Việt và cách gọi quen thuộc trong cộng đồng. |

Ví dụ câu lệnh bạn có thể gõ:

```text
Dịch các mục menu này của A7 IV sang tiếng Việt: Focus Area, Silent Shooting, Anti-flicker Shoot Sel.
```
```text
Rà file ~/Downloads/ILDC_TranslationCheck_VN.xls, chỉ các dòng lỗi, ghi đề xuất ra file mới.
```
```text
Viết blog 1.500 từ "Sony A7 IV hay A7R V", từ khóa chính "Sony A7 IV hay A7R V", độc giả là thợ chụp cưới.
```
```text
Audit SEO AIO bài này: ~/blog/zv-e10-ii-review.md
```

---

## Cài đặt

### Yêu cầu
- [Claude Code](https://code.claude.com)
- [uv](https://docs.astral.sh/uv/) (dùng để chạy MCP server, tự cài Python và thư viện): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Tùy chọn: font Liberation Sans hoặc DejaVu Sans để đo độ rộng chữ chính xác hơn (Linux thường có sẵn).

### Cách 1: cài như plugin (khuyến nghị)
Trong Claude Code:

```text
/plugin marketplace add thaikpham/thaikpham-blogskill
/plugin install sony-alpha-viet@thaikpham-blogskill
```

Khởi động lại Claude Code. Plugin tự đăng ký cả skill lẫn MCP server. Lần chạy đầu, `uv` tải thư viện mất khoảng vài chục giây.

Kiểm tra:
```text
/mcp
```
Phải thấy `sony-alpha-viet` ở trạng thái connected. Hỏi Claude "gọi data_info" để xem đường dẫn dữ liệu đang dùng.

### Cách 2: cài thủ công

```bash
git clone https://github.com/thaikpham/thaikpham-blogskill.git
```
```bash
cd thaikpham-blogskill && uv sync
```
```bash
claude mcp add --scope user sony-alpha-viet -- uv run --directory "$(pwd)" sony-alpha-viet-mcp
```
```bash
ln -s "$(pwd)/skills/sony-alpha-viet" ~/.claude/skills/sony-alpha-viet
```

### Cách 3: chỉ dùng skill, không MCP
Chỉ cần làm bước symlink ở trên. Claude vẫn dịch và viết theo glossary, checklist trong `skills/sony-alpha-viet/references/`, nhưng không có bộ nhớ dịch, không đo được độ rộng chữ, không tự chấm SEO bằng máy. Kết quả dịch menu sẽ được ghi rõ là "chưa kiểm bằng MCP".

---

## Dùng với Gemini, ChatGPT, Meta AI

| Nền tảng | Cách cài | Có công cụ MCP? |
|---|---|---|
| **Gemini CLI** | `gemini extensions install https://github.com/thaikpham/thaikpham-blogskill` | ✅ đầy đủ |
| **ChatGPT** | Custom GPT: dán `portable/system-prompt.md` vào Instructions, tải `portable/knowledge/` vào Knowledge | Chỉ khi bật developer mode + chạy server `--http --read-only` sau HTTPS |
| **Gemini app** | Gem: dán `portable/system-prompt.md`, tải `portable/knowledge/` | ❌ |
| **Llama (Meta)** | `sony-alpha-viet-llama`: agent Llama qua Ollama hoặc Llama API | ✅ (chỉ đọc mặc định) |
| **Meta AI** | Tạo AI riêng bằng Meta AI Studio với `portable/meta-ai-studio/` (nhớ quy tắc trong Instagram/Messenger/WhatsApp), hoặc dán `portable/system-prompt.md` vào chat | ❌ |

**Cách nhanh nhất cho AI có đọc web** (Meta AI, ChatGPT, Gemini): gửi link repo kèm câu
```text
Đọc https://github.com/thaikpham/thaikpham-blogskill và làm theo AGENTS.md. Sau đó: <yêu cầu của bạn>
```
`AGENTS.md` và `llms.txt` chỉ cho AI đọc đúng prompt và file kiến thức. Lưu ý: AI chỉ nhớ trong cuộc trò chuyện đó, và tùy lần, nó có thể chỉ đọc một phần file.

**Llama (Meta) có công cụ thật:** `uv run sony-alpha-viet-llama "Dịch menu: Focus Area, Silent Shooting" -v`. Lệnh này chạy model Llama qua Ollama (mặc định `llama3.2:3b`) hoặc Llama API của Meta (`--base-url https://api.llama.com/compat/v1`, biến `LLAMA_API_KEY`), và gọi công cụ MCP ở chế độ chỉ đọc. Cần tự tải model: `ollama pull llama3.2:3b`.

> Thử thật (03/11/2026): `llama3.2:3b` gọi được công cụ và lấy đúng bản đã duyệt trong bộ nhớ, nhưng hay sinh JSON lỗi và dịch sai chuỗi mới (ví dụ "Range of Zoom Assist" → "Khối lượng zoom hỗ trợ"). Chỉ dùng 3B để thử kết nối. `llama3.1:8b` (`--model llama3.1:8b`, khoảng 35–45 giây/lần trên GPU 4 GB) dịch đúng cả 3 mục thử trong 4/4 lần, nhưng thường bỏ qua `check_translation` và tự nhận đã kiểm tra. Vì vậy agent luôn ghi cuối câu trả lời danh sách công cụ **thật sự** đã chạy, và cảnh báo nếu bản dịch chưa qua `check_translation`. Llama 4 qua Llama API sẽ tốt hơn. Luôn duyệt lại kết quả.

Hướng dẫn từng bước và cảnh báo bảo mật khi mở MCP ra Internet: [`portable/README.md`](portable/README.md).

---

## Dữ liệu và bộ nhớ dịch

MCP lưu toàn bộ kiến thức trong một **thư mục dữ liệu riêng, nằm ngoài repo**:

| Ưu tiên | Đường dẫn |
|---|---|
| 1 | Biến môi trường `SONY_VN_DATA` nếu bạn đặt |
| 2 | Trường `"data"` trong `~/.config/sony-alpha-viet/config.json`. Nên dùng cách này: mọi shell và mọi client (Claude Code, Gemini CLI, agent Llama) đều đọc được, kể cả shell không nạp `~/.bashrc` |
| 3 | `~/.local/share/sony-alpha-viet/data` (hoặc `$XDG_DATA_HOME/sony-alpha-viet/data`): dữ liệu mẫu |

Lần chạy đầu, thư mục này được tạo từ `data-sample/` và khởi tạo git. Nhờ vậy mọi thay đổi đều có lịch sử và hoàn tác được bằng `git revert`.

| File | Nội dung |
|---|---|
| `glossary.json` | Thuật ngữ EN → VI, dạng ngắn, `locked: true` = quyết định đã chốt, ưu tiên cao nhất |
| `rules.json` | Quy tắc thay thế (regex), chuỗi chuẩn, mẫu bị cấm |
| `exceptions.json` | Từ được giữ tiếng Anh: tên Sony, ứng dụng, chuẩn kỹ thuật, viết tắt |
| `keep_english.json` | Thuật ngữ bạn chốt giữ tiếng Anh (Zoom, Time Code, Preset…) |
| `tm.jsonl` | Bộ nhớ dịch: các cặp EN → VI đã duyệt, kèm thông số khung hiển thị |
| `feedback.jsonl` | Mọi lần bạn sửa bản dịch |
| `rules.md` | Quy tắc dịch dạng văn bản, đọc qua `get_guidelines` |
| `LEARNING_LOG.md` | Nhật ký những gì công cụ đã học |

**`data-sample/` không chứa bộ nhớ dịch thật** (`tm.jsonl` rỗng). Chuỗi menu nội bộ từ các dự án dịch cho Sony là dữ liệu của Sony, không đưa lên repo công khai. Glossary, quy tắc và ngoại lệ trong `data-sample/` là thuật ngữ nhiếp ảnh chung, dùng được ngay.

Nếu bạn có dữ liệu riêng, tạo `~/.config/sony-alpha-viet/config.json`:
```json
{ "data": "/đường/dẫn/tới/data" }
```
Hoặc đặt tạm cho một shell: `export SONY_VN_DATA="/đường/dẫn/tới/data"`. Gọi `data_info` để xem đang dùng dữ liệu nào (`data_source`). Agent Llama cũng cảnh báo cuối câu trả lời nếu đang chạy dữ liệu mẫu.
Bộ nhớ càng nhiều chuỗi đã duyệt thì `prepare_batch` càng trả về nhiều bản khớp 100%, và bản dịch càng thống nhất.

Tạo lại `data-sample/` từ dữ liệu riêng (đã lọc bỏ bộ nhớ dịch và mã chuỗi nội bộ):
```bash
uv run python scripts/export_public_data.py --src "$SONY_VN_DATA" --out data-sample
```

---

## Cách dùng

Skill tự kích hoạt khi bạn nói "dịch menu Sony", "dịch hướng dẫn Sony", "viết blog Sony Alpha", "SEO AIO tiếng Việt", "audit bài viết", hoặc nhắc tới OSD, ILDC, TranslationCheck, A7/A7R/A7S/A6xxx/ZV/FX. Gọi trực tiếp bằng `/sony-alpha-viet:sony-alpha-viet` (cài dạng plugin) hoặc `/sony-alpha-viet` (cài thủ công).

Claude xác định chế độ trước khi làm. Nếu thiếu thông tin quan trọng (model máy, ngôn ngữ nguồn, từ khóa chính), Claude **hỏi một lượt** trước khi viết nội dung dài. Yêu cầu ngắn mà ngữ cảnh đã rõ thì làm luôn.

### Chế độ A: dịch menu máy ảnh

**Quy trình Claude thực hiện:**

```
get_guidelines ─► prepare_batch ─► dịch ─► check_translation ─► bảng + CSV
   (quy tắc)      (bộ nhớ + thuật    (chuỗi   (tự sửa, đo độ rộng,     │
                   ngữ cho mỗi chuỗi) còn lại) gợi ý rút gọn)           ▼
                                                    bạn duyệt / sửa ─► ghi nhớ
```

1. **`prepare_batch`**: với mỗi chuỗi, trả về bản khớp 100% trong bộ nhớ (nếu có), các bản gần giống và thuật ngữ liên quan (thuật ngữ khóa đứng đầu).
2. **Dịch** phần chưa có, bám thuật ngữ và các bản gần giống để giữ thống nhất.
3. **`check_translation`** kiểm từng chuỗi và tự sửa những gì sửa được. Các lỗi nó bắt:
   - sót tiếng Anh, trộn Anh–Việt;
   - dùng từ bị cấm ("cửa trập", "nút màn trập"…);
   - viết tắt rụng chữ ("ság", "đ.ký"), dính chữ;
   - mất biến `${v1}`, mất icon `<cE660>`, sai số dòng;
   - dùng dấu phẩy thập phân thay vì dấu chấm (0.3EV);
   - không khớp với bản đã duyệt;
   - tràn khung màn hình.

   Khi chuỗi tràn (BORDER/OVER), công cụ trả thêm `short_candidates`: các bản rút gọn đã đo độ rộng sẵn.
4. **Xuất** bảng `STT | Nguồn | Tiếng Việt | Loại UI | Ghi chú` và file CSV.

**Ví dụ:**

| English | Tiếng Việt | Ghi chú |
|---|---|---|
| Aperture | Khẩu độ | Bộ nhớ đã duyệt, thuật ngữ khóa |
| Shutter Speed | Tốc độ màn trập | Chiếm 62% khung |
| Range of Zoom Assist | Dải hỗ trợ Zoom | Zoom giữ tiếng Anh (keep_english) |
| Anti-flicker Shoot Sel. | Chống nhấp nháy | "Chọn chụp chống nhấp nháy" tràn khung, bỏ từ menu đã ngầm hiểu |

**Làm việc với file Sony `*_TranslationCheck_VN.xls`:**
- `xls_read(path, only_flagged=True)`: chỉ lấy các dòng đang vi phạm quy tắc, kèm thông số khung.
- `xls_write(src, out, proposals)`: chỉ ghi cột **AN** (bản đề xuất), **AU** (loại lỗi, đúng dropdown của Sony) và **AV** (lý do bằng tiếng Anh). Luôn ghi ra file mới, phần còn lại của file giữ nguyên từng byte.

**Về đo độ rộng:** đây là **ước lượng** bằng font thay thế, đã hiệu chỉnh theo font máy Sony. Từ 92% khung trở xuống là an toàn. Kết quả BORDER/OVER cần xác nhận lại bằng SonyTool.

### Chế độ B: dịch tài liệu

- Giữ nguyên cấu trúc gốc: heading, danh sách, bảng.
- Tên mục menu được **in đậm**, ghi đúng như trên máy tiếng Việt. Lần đầu xuất hiện kèm tên gốc nếu người đọc có thể dùng máy tiếng Anh: **Vùng lấy nét** (Focus Area).
- Đường dẫn menu viết dạng **MENU → Lấy nét → AF/MF → Vùng lấy nét**.
- Sau khi dịch, có một lượt biên tập riêng để bỏ văn dịch máy: câu bị động thừa, câu mở bằng "Việc…", chuỗi "của" dày đặc, câu quá dài. Công cụ `style_lint` bắt các lỗi này tự động.
- Cuối bản dịch liệt kê các thuật ngữ mới để bạn chốt.

### Chế độ C: viết và chấm blog SEO + AIO

**Quy trình:**

1. **Brief**: search intent, từ khóa chính/phụ, các câu hỏi kiểu People Also Ask, outline H2/H3, link dự kiến. Bài trên 1.000 từ thì Claude trình outline cho bạn duyệt trước.
2. **Viết** theo `templates/blog-post-template.md`:
   - TL;DR 40–70 từ ngay dưới tiêu đề;
   - mỗi H2 mở bằng câu trả lời 1–2 câu có thể trích riêng;
   - có bảng, checklist, FAQ 3–6 câu và ví dụ thực tế cho người dùng Việt Nam.
3. **Tra thuật ngữ** bằng `lookup_prose_term`. Văn xuôi dùng cách gọi quen thuộc (full-frame, lấy nét mắt (Eye AF)), khác với chuẩn thuần Việt của menu.
4. **Kiểm văn phong** bằng `style_lint`: cụm "AI-sounding" ("Hãy cùng khám phá", "đưa trải nghiệm lên tầm cao mới"…), dấu hiệu văn dịch máy, câu dài, sai thuật ngữ, sai dấu thập phân.
5. **Chấm điểm** bằng `seo_audit`: trả bảng `Mục | Kết quả | Bằng chứng | Cách sửa` và điểm số. Những mục máy không tự chấm được thì ghi "Cần người duyệt".
6. **Sinh Schema** bằng `faq_schema`: JSON-LD gồm `Article` và `FAQPage`. Câu hỏi và câu trả lời trong Schema lấy nguyên văn từ bài, đúng yêu cầu của Google.
7. **Slug** bằng `slugify`: "Sony A7 IV hay A7R V" → `sony-a7-iv-hay-a7r-v`.

**Nguyên tắc cứng:** không bịa thông số, giá, ngày ra mắt hay kết quả benchmark. Thông số chưa đối chiếu được ghi `[cần xác minh]`. Giá bán ở Việt Nam luôn ghi `[cần xác minh]` trừ khi bạn cung cấp. `seo_audit` coi bài còn dấu `[cần xác minh]` là **chưa hoàn chỉnh**.

**Checklist SEO/AIO (tóm tắt 23 mục, bản đầy đủ ở `references/seo-aio-checklist.md`):**

| Nhóm | Kiểm tra |
|---|---|
| Từ khóa & meta | Từ khóa chính có ở H1, slug, 100 từ đầu, một H2, meta description; meta title 50–60 ký tự; description 140–160 ký tự; không nhồi từ khóa (≤ 1,5%) |
| Cấu trúc | TL;DR 40–70 từ; một H1; heading không nhảy cấp; có bảng hoặc checklist; kết luận có hành động cụ thể |
| AIO | FAQ 3–6 câu, mỗi câu trả lời 40–70 từ và tự đứng được; có định nghĩa một câu; câu chứa số liệu nêu rõ chủ thể |
| E-E-A-T | Không có số liệu chưa kiểm chứng; 1–3 nguồn ngoài uy tín; 2–5 link nội bộ; có tác giả và ngày cập nhật |
| Schema & ảnh | Article + FAQPage khớp nguyên văn với bài; ảnh có alt text |
| Ngôn ngữ | Thuật ngữ đúng glossary; không văn dịch máy; không có cụm "AI-sounding" |

Xem bài mẫu đầy đủ, kèm bảng tự audit, tại `skills/sony-alpha-viet/examples/example-blog-post.md`.

---

## Quy tắc thuật ngữ

Một thuật ngữ có thể có **hai chuẩn**, tùy nơi dùng:

| EN | Menu máy (chế độ A) | Bài viết / tài liệu (B, C) |
|---|---|---|
| Full Frame | Toàn khung | full-frame |
| Eye AF | Eye AF | lấy nét mắt (Eye AF) |
| Picture Profile | Picture Profile | Picture Profile (hồ sơ hình ảnh) |
| Image Stabilization | Ổn định hình ảnh / SteadyShot | chống rung trên thân máy (IBIS) |
| Zoom | Zoom | zoom |
| Mechanical Shutter | Màn trập cơ | màn trập cơ |

**Menu máy:**
- Dùng tiếng Việt, không trộn Anh–Việt. Có hai ngoại lệ:
  - tên riêng và chuẩn kỹ thuật (Sony, S-Log3, XAVC S, HDMI, ISO…);
  - thuật ngữ trong danh sách **keep_english**.
- Thuật ngữ đã khóa (🔒) thắng mọi quy tắc khác. Ví dụ: shutter = màn trập, Shutter Button = nút chụp, Tracking = theo dõi, Defocus = xóa phông.
- Viết hoa kiểu câu (chỉ chữ đầu). Không viết tắt rụng chữ.

**Bài viết:** giữ những thuật ngữ tiếng Anh mà nhiếp ảnh gia Việt quen dùng, kèm giải nghĩa ở lần xuất hiện đầu tiên.

**Chính sách keep_english:** một thuật ngữ được giữ tiếng Anh khi bản tiếng Việt **không giúp người dùng hiểu hơn**. Hiện gồm Zoom, Time Code, Preset; Firmware nằm trong danh sách ngoại lệ chung. Viết hoa theo bản gốc: tên mục "Zoom Assist" → "Zoom", câu trợ giúp "zoom speed" → "tốc độ zoom". Khi bạn chốt thêm một thuật ngữ, công cụ `keep_english` sẽ:
1. Cho xem trước bao nhiêu chuỗi trong bộ nhớ, bao nhiêu quy tắc và thuật ngữ bị ảnh hưởng.
2. Khi bạn đồng ý: sửa toàn bộ bộ nhớ, tắt các quy tắc xung đột, khóa thuật ngữ. Từ đó trở đi, bộ kiểm tra báo lỗi nếu bản dịch lại dùng từ tiếng Việt cũ.

Glossary đầy đủ (EN, JP, Menu, Bài viết, Ghi chú) nằm ở `skills/sony-alpha-viet/references/glossary-vi.md`.

---

## Tự học từ lần sửa của bạn

| Bạn làm | Claude gọi | Kết quả |
|---|---|---|
| Chốt một thuật ngữ: "dùng X cho Y" | `record_term` | Thuật ngữ được khóa, ưu tiên cao nhất |
| Sửa một bản dịch | `record_feedback` | Bộ nhớ cập nhật; cụm từ bị sửa được ghi lại |
| Sửa cùng một cụm ≥ 2 lần, hoặc nói "từ nay luôn…" | `learn` | Cụm đó thành quy tắc tự sửa |
| Rút gọn một bản dịch bị tràn | `record_feedback` | Học quy tắc rút gọn, **chỉ áp khi chuỗi tràn khung** |
| Giữ một từ tiếng Anh | `record_feedback` → `keep_english` | Đề xuất đưa vào danh sách giữ tiếng Anh, xem trước rồi áp toàn bộ |
| Cấm một cách dịch | `ban_term` | Mọi bản dịch dùng từ đó bị báo lỗi |
| Duyệt bản dịch, không sửa | `remember_translation` | Lưu vào bộ nhớ |

Cuối mỗi phiên, Claude gọi `learn` → `review_memory` (tìm quy tắc thừa hoặc mâu thuẫn) → `commit_memory` (commit thư mục dữ liệu vào git). Claude chỉ ghi nhớ khi bạn đã đồng ý, và không tự đổi thuật ngữ đã khóa.

---

## Danh sách công cụ MCP

| Nhóm | Công cụ | Việc làm |
|---|---|---|
| Thông tin | `data_info` | Đường dẫn dữ liệu, số thuật ngữ, quy tắc, chuỗi; đang dùng dữ liệu mẫu hay dữ liệu riêng |
| | `get_guidelines(section)` | Quy tắc dịch, ngoại lệ, thuật ngữ khóa, danh sách keep_english, nhật ký học |
| Tra cứu | `lookup_term`, `search_memory`, `prepare_batch` | Tra glossary menu, tìm bản dịch gần giống, chuẩn bị dịch hàng loạt |
| | `lookup_prose_term` | Tra thuật ngữ cho bài viết (EN/JP → cách gọi trong menu và trong văn xuôi) |
| Kiểm tra menu | `check_translation` | Kiểm, tự sửa, đo độ rộng, gợi ý rút gọn |
| | `check_fit`, `suggest_short` | Đo độ rộng một chuỗi; sinh các bản rút gọn vừa khung |
| Ghi nhớ | `record_term`, `record_feedback`, `remember_translation`, `ban_term`, `keep_english` | Lưu quyết định của bạn |
| Tự cải tiến | `learn`, `review_memory`, `disable_rule`, `commit_memory` | Biến lần sửa thành quy tắc, rà soát, lưu lịch sử |
| File Sony | `xls_read`, `xls_write` | Đọc/ghi `*_TranslationCheck_VN.xls` (chỉ cột AN/AU/AV) |
| Blog | `slugify`, `count_words`, `style_lint`, `seo_audit`, `faq_schema` | Tạo slug, đếm từ (bỏ bảng, code, frontmatter), kiểm văn phong, chấm SEO/AIO, sinh JSON-LD |

**Resources:** các file trong `references/` và `templates/` của skill, đọc qua địa chỉ `sony-alpha-viet://references/<tên file>` và `sony-alpha-viet://templates/<tên file>`.

**Prompts** (gõ `/` trong Claude Code để thấy):
- `translate_menu(model, source_lang, strings)`
- `write_blog(topic, primary_keyword, audience, models, length)`
- `audit_post(path_or_text)`

---

## Cấu trúc repo

```
.claude-plugin/          plugin.json, marketplace.json
.mcp.json                đăng ký MCP server cho plugin Claude Code
AGENTS.md, llms.txt      chỉ dẫn cho AI đọc repo qua link (Meta AI, ChatGPT, Gemini)
gemini-extension.json    extension Gemini CLI (+ GEMINI.md)
portable/                system-prompt.md + knowledge/ cho ChatGPT, Gemini app, Meta AI
skills/sony-alpha-viet/
  SKILL.md               quy trình 3 chế độ, nguyên tắc dịch và viết
  references/
    glossary-vi.md       thuật ngữ EN/JP → Menu / Bài viết
    sony-menu-terms.md   quy trình dịch menu, file xls, tự học, giới hạn firmware
    seo-aio-checklist.md 23 tiêu chí SEO/AIO
    writing-style-vi.md  văn phong, chống văn dịch máy, số và đơn vị
  templates/             blog-post-template.md, menu-translation-table.csv, faq-schema.json
  examples/              example-menu-translation.md, example-blog-post.md (kèm bảng audit)
src/sony_alpha_viet/     MCP server: core (quy tắc, kiểm tra, độ rộng), memory (tự học), blog (SEO/AIO), xls
data-sample/             dữ liệu khởi tạo công khai (không có bộ nhớ dịch)
scripts/                 export_public_data.py, build_portable.py
tests/
```

---

## Giới hạn và an toàn

- **Firmware:** skill chỉ dịch và chuẩn hóa text. Nó không sửa, đóng gói hay flash firmware, và không bật service mode hay mở khóa ngôn ngữ. Chỉ khi bạn tự cung cấp file và xác nhận rõ, Claude mới trích và dịch chuỗi, rồi ghi ra file mới. Các dự án PMCA-RE, Sony-PMCA-RE, OpenMemories-Tweak chỉ được nhắc tới như tài liệu tham khảo.

  > ⚠️ Can thiệp firmware hoặc dùng công cụ không chính thức có thể làm **mất bảo hành**, **hỏng máy**, và có thể vi phạm điều khoản sử dụng của Sony.

- **Độ rộng chữ** là ước lượng. Kết quả BORDER/OVER cần xác nhận bằng SonyTool.
- **Thông số và giá** trong bài blog phải đối chiếu nguồn chính thức trước khi đăng.
- **Dữ liệu dự án của Sony** (bộ nhớ dịch, file TranslationCheck) chỉ lưu trên máy bạn, không đưa vào repo.

---

## Câu hỏi thường gặp

**Không thấy công cụ `mcp__sony-alpha-viet__*`?**
Chạy `/mcp` để xem trạng thái. Kiểm tra máy đã có `uv` (`uv --version`) chưa. Lần đầu khởi động cần mạng để `uv` tải thư viện.

**Đã sửa dữ liệu bằng tay hoặc vừa cập nhật plugin, nhưng Claude vẫn dùng dữ liệu cũ?**
MCP server giữ dữ liệu trong bộ nhớ khi chạy. Vào `/mcp`, chọn `sony-alpha-viet` → reconnect. Đừng để hai phiên Claude cùng ghi một thư mục dữ liệu khi một phiên đang chạy server cũ: lần ghi sau có thể đè lên lần ghi trước.

**Hoàn tác một thay đổi bộ nhớ?**
Thư mục dữ liệu là một repo git: `git -C "$SONY_VN_DATA" log`, rồi `git revert <commit>`. Muốn tắt một quy tắc sai thì dùng `disable_rule`.

**Dịch từ tiếng Nhật được không?**
Được. Glossary có cột JP để nhận diện thuật ngữ. Claude dịch theo nghĩa, và đối chiếu với bản tiếng Anh của cùng model nếu có.

**Tôi không dịch cho Sony, chỉ viết blog. Có cần MCP không?**
Không bắt buộc. Nhưng `seo_audit`, `style_lint`, `faq_schema` giúp chấm bài chính xác: đếm ký tự, đếm từ, kiểm Schema khớp nguyên văn. Đây là những việc người dễ sót.

**Đổi quy tắc cho riêng mình?**
Chốt bằng lời với Claude (Claude sẽ gọi `record_term`, `ban_term`, `keep_english`), hoặc sửa `glossary-vi.md` và `writing-style-vi.md` trong skill.

---

## Phát triển

```bash
uv sync
```
```bash
uv run pytest -q
```

| Biến môi trường | Ý nghĩa |
|---|---|
| `SONY_VN_DATA` | Thư mục dữ liệu (mặc định `~/.local/share/sony-alpha-viet/data`) |
| `SONY_VN_FONT` | Font dùng để đo độ rộng chữ (mặc định Liberation Sans) |

Chạy server qua HTTP (cho ChatGPT developer mode / client MCP từ xa): `uv run sony-alpha-viet-mcp --http --read-only --port 8765` → endpoint `/mcp`.

Phát triển từ dự án dịch menu Sony ILDC (2026) và các skill tham khảo: claude-translation-skill, vietnamese-language-skill, ChuotVan, claude-blog, claude-seo, ai-seo.

Tác giả: **Pham Khang Thai**. Giấy phép MIT.
