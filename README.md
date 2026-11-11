# Sony Alpha Việt

Bộ quy tắc, bảng thuật ngữ và công cụ để AI dịch menu, tài liệu máy ảnh Sony Alpha sang tiếng Việt như một biên tập viên, và viết blog máy ảnh chuẩn SEO + AIO.

**Tác giả:** Pham Khang Thai (Thái) · **Phiên bản:** 1.4.0 · **Giấy phép:** MIT

## Dùng ngay: dán một dòng vào bất kỳ AI nào

Mở ChatGPT, Gemini, Claude hoặc Meta AI, dán dòng này rồi thêm yêu cầu của bạn:

```
Đọc https://raw.githubusercontent.com/thaikpham/alphaskill/main/llms-full.txt và làm theo hướng dẫn trong đó. Sau đó: [yêu cầu của bạn]
```

Ví dụ yêu cầu:

- `Dịch các chuỗi menu này sang tiếng Việt: Focus Area, Zebra Display, Aperture Priority (khung hẹp)`
- `Dịch đoạn hướng dẫn sau sang tiếng Việt, tên menu in đậm kèm tiếng Anh: …`
- `Rà bản dịch này, chỉ ra chỗ sai thuật ngữ và chỗ còn giọng dịch máy: …`

`llms-full.txt` là file lõi (khoảng 93 KB) gồm vai trò, quy tắc dịch, văn phong, 666 thuật ngữ và ví dụ dịch trước–sau. Hai file bổ sung, thêm vào câu lệnh khi cần:

| Việc | Đọc thêm |
|---|---|
| Viết hoặc chấm blog SEO/AIO | `https://raw.githubusercontent.com/thaikpham/alphaskill/main/llms-blog.txt` |
| Kiến thức nhiếp ảnh, giáo án, trả lời học viên | `https://raw.githubusercontent.com/thaikpham/alphaskill/main/llms-knowledge.txt` |

Nếu AI không mở được link: tải [llms-full.txt](llms-full.txt) về rồi đính kèm vào cuộc trò chuyện.

**Giới hạn của cách này.** AI chỉ có văn bản, không có công cụ. Nó không đo được chuỗi có tràn khung hay không, không đọc file `.xls` của Sony, không ghi nhớ bản sửa của bạn và không chấm blog bằng máy. Thông số và giá sẽ được ghi `[cần xác minh]` thay vì đoán. Cần các việc đó thì cài bản đầy đủ ở dưới.

## Làm được gì

| Chế độ | Việc | Kết quả |
|---|---|---|
| A · Dịch menu | Chuỗi menu EN/JP → VI, rà file `ILDC_TranslationCheck_VN.xls` | Bảng nguồn, bản dịch, ghi chú; dạng ngắn cho khung hẹp; file Sony mới khi có MCP |
| B · Dịch tài liệu | Help Guide, hướng dẫn, mô tả sản phẩm | Văn xuôi tự nhiên, tên menu in đậm kèm tiếng Anh, bảng thuật ngữ đã dùng |
| C · Blog SEO + AIO | Viết và chấm bài theo checklist 40 tiêu chí | Bài có TL;DR, bảng so sánh, FAQ, JSON-LD |
| D · Đào tạo | Kiến thức nhiếp ảnh, giáo án, câu hỏi học viên | Trả lời theo kho kiến thức, có cách giảng |

## Chọn cách dùng

| Cách | Cài đặt | Thuật ngữ + quy tắc | Đo khung chữ | Đọc/ghi file Sony `.xls` | Ghi nhớ bản sửa |
|---|---|---|---|---|---|
| Dán một link | Không | Có | Không | Không | Không |
| Custom GPT / Gem / Meta AI Studio | Tải file lên một lần | Có | Không | Không | Không |
| API công khai | Không | Có | Có | Không | Không |
| Claude Code hoặc Gemini CLI | 2 phút | Có | Có | Có | Có |

Dịch menu cho dự án Sony thật nên dùng Claude Code hoặc Gemini CLI: chỉ bản này có bộ nhớ dịch, đo khung và xuất file đúng định dạng Sony.

### Claude Code

```
/plugin marketplace add thaikpham/alphaskill
/plugin install sony-alpha-viet@alphaskill
```

Khởi động lại Claude Code, gõ `/mcp` và kiểm tra `sony-alpha-viet` ở trạng thái connected.

### Gemini CLI

```
gemini extensions install https://github.com/thaikpham/alphaskill
```

### Custom GPT, Gem, Meta AI Studio

Dán `portable/system-prompt.md` vào phần Instructions và tải các file trong `portable/knowledge/` lên. Hướng dẫn từng nền tảng: [portable/README.md](portable/README.md).

### API công khai

`https://api.alphacolorlab.com` chỉ đọc, không cần tài khoản. Dữ liệu là bản công khai trong `data-sample/`.

- Danh sách công cụ và tham số: `GET /v1` (27 công cụ chỉ đọc trong tổng 45 công cụ MCP)
- Tra thuật ngữ: `GET /v1/lookup_term?text=Focus%20Area`
- Kiểm bản dịch: `POST /v1/check_translation` với JSON `{"en": "Focus Area", "vi": "Vùng lấy nét"}`
- Client MCP: thêm server `https://api.alphacolorlab.com/mcp`

Các công cụ ghi dữ liệu (ghi nhớ, sửa file Sony, ghi Obsidian) chỉ có khi cài trên máy.

## Ví dụ với bản đầy đủ

Dịch menu:

```
Dịch 3 chuỗi này cho A7 IV: Focus Area, Silent Mode, Zebra Display
```

Rà file Sony:

```
Rà file ~/Downloads/ILDC_TranslationCheck_VN.xls, chỉ lấy dòng lỗi, xuất ra ~/Desktop/fixed.xls
```

Dịch tài liệu:

```
Dịch file ~/a7iv-help-guide.pdf sang tiếng Việt tự nhiên, giữ heading, tên menu in đậm
```

Viết blog:

```
Viết blog 1500 từ "Sony A7 IV hay A7R V cho thợ cưới", từ khóa "Sony A7 IV hay A7R V", độc giả thợ cưới TP.HCM
```

## Nguyên tắc dịch

- **Tra trước, dịch sau.** Mọi thuật ngữ giao diện lấy từ bảng thuật ngữ. Không có trong bảng thì dịch, đánh dấu `[thuật ngữ mới]` và chờ người duyệt.
- **Bản sửa đã duyệt thắng bảng thuật ngữ.** Quy tắc thay thế là quyết định mới nhất của người dùng. Ví dụ Zebra Display → "Hiển thị sọc vằn".
- **Menu và văn xuôi dùng dạng khác nhau.** Menu ngắn, không dấu chấm cuối; bài viết dùng cách gọi quen tai.

| EN | Menu | Bài viết |
|---|---|---|
| Focus Area | Vùng lấy nét | vùng lấy nét |
| Exposure Comp. | Bù sáng | bù sáng |
| Eye AF | Eye AF | lấy nét mắt (Eye AF) |
| Time Code, Zoom, Preset | giữ tiếng Anh | giữ tiếng Anh |

- **Chống giọng dịch máy.** Bỏ bị động thừa, bỏ "việc" mở câu, tách câu dài, trật tự từ tiếng Việt. Ví dụ trước–sau: [example-doc-translation.md](skills/sony-alpha-viet/examples/example-doc-translation.md).
- **Không bịa thông số, giá, ngày ra mắt.** Chưa đối chiếu nguồn Sony chính thức thì ghi `[cần xác minh]`.
- **Giọng thương hiệu Sony** áp dụng cho blog và tư vấn; khi dịch thì trung thành bản gốc. Chi tiết: [sony-core-principles.md](skills/sony-alpha-viet/references/sony-core-principles.md).
- **Firmware:** chỉ dịch văn bản. Không sửa, không flash firmware, không bật service mode.

## Viết blog AIO-first

AIO (AI Overviews) là viết để Google AI Overviews, ChatGPT, Perplexity, Gemini trích bài của bạn trong câu trả lời. Bài cần TL;DR 40–70 từ ngay dưới H1, mỗi H2 mở bằng câu trả lời tự đứng được, bảng so sánh, FAQ 3–6 câu và số liệu có nguồn.

Checklist đầy đủ 40 tiêu chí (10 SEO nền tảng, 15 AIO cốt lõi, 10 schema và kỹ thuật, 5 giọng thương hiệu): [seo-aio-checklist.md](skills/sony-alpha-viet/references/seo-aio-checklist.md). Bài mẫu: [example-blog-post.md](skills/sony-alpha-viet/examples/example-blog-post.md).

| Công cụ | Việc |
|---|---|
| `paa_generator` | Gợi ý 10 câu hỏi People Also Ask theo mẫu (offline) |
| `style_lint` | Bắt cụm văn AI, bị động, câu dài, sai thuật ngữ |
| `seo_audit` | Chấm nền tảng SEO |
| `aio_audit` | Chấm tự động 10 mục AIO cốt lõi, điểm 0–100. Điểm là tỉ lệ mục đạt, không phải xác suất được AI trích |
| `citation_checker` | Kiểm link nguồn còn sống và có phải nguồn uy tín |
| `freshness_check` | Báo bài cũ bao lâu, gợi ý cập nhật |
| `brand_voice_checker` | Kiểm 5 tiêu chí giọng thương hiệu Sony |
| `faq_schema` | Sinh JSON-LD Article + FAQPage |

Các tiêu chí còn lại trong checklist phải tự rà bằng mắt.

## Dữ liệu

| Loại | Ở đâu | Công khai |
|---|---|---|
| Bảng thuật ngữ, quy tắc, ngoại lệ, kho kiến thức đã xuất bản | `data-sample/` | Có |
| Bộ nhớ dịch Sony, tài liệu Sony đã nạp | repo riêng `alphaskill-data`, trỏ qua `SONY_VN_DATA` | Không |

Không có dữ liệu riêng, MCP chạy trên `data-sample/`: vẫn tra thuật ngữ và kiểm quy tắc, nhưng không có bộ nhớ dịch.

## Cho người phát triển

```bash
uv sync
```

```bash
uv run pytest -q
```

```bash
uv run python scripts/build_portable.py
```

- `skills/sony-alpha-viet/`: SKILL.md, tài liệu tham chiếu, ví dụ. Đây là nguồn gốc của mọi quy tắc.
- `src/sony_alpha_viet/`: MCP server.
- `llms-*.txt`, `portable/knowledge/`: sinh tự động bởi `scripts/build_portable.py`, không sửa tay. `--check` báo lỗi khi file sinh ra bị cũ.
- Chạy API trên máy: `uv run sony-alpha-viet-mcp --http --read-only --port 8765`.
- Hướng dẫn cho AI đọc repo: [AGENTS.md](AGENTS.md), [llms.txt](llms.txt).

Lịch sử thay đổi: [CHANGELOG.md](CHANGELOG.md).
