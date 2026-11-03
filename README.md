# Sony Alpha Việt — Trợ lý dịch menu & viết blog Sony cho người Việt

> Bạn chụp Sony A7, A7R, A7S, A6xxx, ZV, FX? Bạn cần menu tiếng Việt chuẩn, tài liệu dễ hiểu, và bài blog chuẩn SEO? Đây là bộ công cụ dành cho bạn.

**Tác giả:** Pham Khang Thai (Thái) — Giấy phép MIT  
**Phiên bản:** 1.3.0 - API công khai, xuất bài Alpha ColorLab, repo dữ liệu riêng 11/2026

---
---

## 💎 Nguyên tắc cốt lõi: Luôn bảo vệ Sony - Tự hào công nghệ tiên phong

Chi tiết đầy đủ: `skills/sony-alpha-viet/references/sony-core-principles.md`

---
---

## Dùng để làm gì?

| Bạn là | Ứng dụng |
| :--- | :--- |
| **Thợ dịch Sony** | Đọc `ILDC_TranslationCheck_VN.xls`, chỉ ra dòng lỗi, gợi ý bản vừa khung, xuất file mới AN/AU/AV đúng chuẩn Sony. |
| **Blogger / YouTuber** | Viết bài "A7 IV hay A7R V cho thợ cưới?" có TL;DR, bảng so sánh, FAQ, tự chấm 35 tiêu chí AIO-first, sinh Schema để AI trích. |
| **Shop máy ảnh** | Dịch mô tả, FAQ, hướng dẫn nhanh, đảm bảo 1 bộ thuật ngữ trên mọi kênh. |
| **Người dùng thường** | Tra `Focus Area là gì?` → `Vùng lấy nét` + giải thích. |

---

## Nên dùng với AI nào?

### 🥇 TỐT NHẤT: Claude Code
Có đủ Skill + MCP. Đo được độ rộng chữ, đọc Excel, tự học từ lần bạn sửa, chấm AIO chính xác. Dùng cho dự án dịch Sony chuyên nghiệp.

### 🥈 TỐT: Gemini CLI
Có đủ MCP như Claude, phù hợp nếu bạn quen hệ Gemini.

### 🥉 DÙNG ĐƯỢC: Meta AI, ChatGPT, Gemini App
Không có MCP, chỉ tra cứu + viết blog. Không đo khung, không đọc Excel. Dùng câu thần chú:
```
Đọc https://github.com/thaikpham/alphaskill và làm theo AGENTS.md. Sau đó: [câu hỏi của bạn]
```

### 🌐 Không cài gì: API dùng chung `https://api.alphacolorlab.com`
Chỉ đọc, ai cũng dùng được (Sony staff, shop, web khác). Dữ liệu là repo public [alphaskill-data](https://github.com/thaikpham/alphaskill-data).
- Danh sách tool và tham số: `GET /v1`
- Gọi tool: `GET /v1/lookup_term?text=Focus%20Area` hoặc `POST /v1/check_translation` với JSON `{"en": "Focus Area", "vi": "Vùng lấy nét"}`
- Client MCP (Claude, ChatGPT developer mode): thêm server `https://api.alphacolorlab.com/mcp`

Các tool ghi dữ liệu (ghi nhớ, sửa file Sony, ghi Obsidian) chỉ có khi cài trên máy.

---

## Cài đặt 2 phút (cho người mới)

### Claude Code:
```
/plugin marketplace add thaikpham/alphaskill
/plugin install sony-alpha-viet@alphaskill
# Khởi động lại Claude Code
/mcp  # phải thấy connected
```

### Gemini CLI:
```
gemini extensions install https://github.com/thaikpham/alphaskill
```

### Meta AI / ChatGPT (không cài gì):
1. Copy `portable/system-prompt.md`
2. Dán vào Instructions của Custom GPT / Meta AI Studio
3. Upload `portable/knowledge/`
4. Chat: `Dịch Focus Area sang tiếng Việt`

---

## ⭐ NÂNG CẤP LỚN 1.1.0: AIO-first - Viết để AI trích dẫn bạn

### Tại sao AIO quan trọng hơn SEO năm 2026?

- **SEO cũ (2015-2023):** Viết để lên top 1 Google, người dùng click vào.
- **AIO mới (2024-2026):** Viết để được **Google AI Overviews, ChatGPT, Perplexity, Gemini** trích dẫn thẳng trong câu trả lời. Người dùng không click, họ đọc luôn đáp án của AI. Nếu bài bạn không có cấu trúc để AI hiểu, bạn mất 68% traffic.

**Checklist cũ 23 tiêu chí → Checklist mới 35 tiêu chí AIO-first:**

### Nhóm 1: Nền tảng SEO (vẫn cần, 10 mục)
1.  Từ khóa chính ở H1, slug, 100 từ đầu, 1 H2, meta description
2.  Meta title 50-60 ký tự, description 140-160 ký tự, có số/năm nếu phù hợp (VD: 2026)
3.  Một H1 duy nhất, heading không nhảy cấp (H2→H3, không H2→H4)
4.  Mật độ từ khóa ≤1.5%, không nhồi
5.  2-5 link nội bộ, 1-3 link ngoài uy tín (Sony official, DPReview, PetaPixel)
6.  Ảnh có alt text mô tả, có WebP, lazy-load
7.  Tốc độ tải <2s, mobile-friendly
8.  Slug ngắn, không dấu: `sony-a7-iv-hay-a7r-v` không phải `sony-a7-iv-hay-a7r-v-cho-tho-cuoi-2026`
9.  Ngày xuất bản + ngày cập nhật rõ ràng
10. Có tác giả thật, có trang About tác giả (E-E-A-T)

### Nhóm 2: AIO Core - Để AI trích dẫn (15 mục - QUAN TRỌNG NHẤT)
11. **TL;DR 40-70 từ ngay dưới H1:** Trả lời thẳng câu hỏi chính trong 1 đoạn. VD: "A7 IV tốt hơn cho thợ cưới vì... A7R V tốt hơn cho phong cảnh vì..." — Đây là thứ AI Overviews copy đầu tiên.
12. **Mỗi H2 mở bằng câu trả lời 1-2 câu có thể đứng một mình:** Không mở bằng "Trong phần này chúng ta sẽ...". AI trích từng H2 riêng lẻ.
13. **Định nghĩa 1 câu cho mọi thuật ngữ mới:** "Khẩu độ là độ mở của ống kính, quyết định lượng sáng vào cảm biến." — AI thích định nghĩa ngắn.
14. **FAQ 3-6 câu, mỗi câu trả lời 40-70 từ, tự đứng được:** Câu hỏi phải là câu người dùng thật sự gõ trên Google/ChatGPT: "A7 IV có chống rung không?", "A7R V chụp cưới có quá nặng không?". Trả lời không được "Xem ở trên" hay "Như đã nói".
15. **Bảng so sánh:** AIO ưu tiên bảng hơn đoạn văn. Mọi bài so sánh phải có bảng `Tiêu chí | A7 IV | A7R V`.
16. **Số liệu phải có chủ thể + nguồn:** Sai: "61MP rất cao". Đúng: "A7R V có cảm biến 61MP (nguồn: Sony official spec 2024)".
17. **Không có `[cần xác minh]`:** AIO coi bài có placeholder là chưa hoàn chỉnh, không trích.
18. **Checklist / Pros-Cons:** "Ưu điểm A7 IV: ..." dạng bullet, AI dễ trích thành list.
19. **Ví dụ thực tế cho người Việt:** "Thợ cưới ở HCM chụp tiệc 5 tiếng với A7 IV + 35mm f/1.4..." — Tăng E-E-A-T.
20. **Câu hỏi People Also Ask (PAA):** Tool mới `paa_generator` sẽ gợi ý 10 câu hỏi liên quan từ Google/Perplexity để bạn trả lời sẵn.
21. **Ngôn ngữ tự nhiên, bỏ AI-sounding:** Cấm "Hãy cùng khám phá", "đưa trải nghiệm lên tầm cao mới", "tối ưu hóa". Tool `style_lint` sẽ bắt.
22. **Entity rõ ràng:** Mỗi khi nhắc A7 IV, phải gắn với Sony, full-frame, 33MP. Để AI hiểu entity, không nhầm.
23. **Freshness:** Ghi "Cập nhật 11/2026: Giá A7 IV hiện..." — AIO ưu tiên bài mới.
24. **Đa phương tiện có transcript:** Video YouTube nhúng phải có transcript tiếng Việt để AI đọc.
25. **Không quảng cáo trá hình:** AIO phạt nặng bài PR lộ liễu.

### Nhóm 3: Schema & Kỹ thuật AIO (10 mục - MỚI)
26. **Schema JSON-LD không chỉ Article + FAQPage:** Thêm `HowTo` (cho bài hướng dẫn cài đặt), `Product` (có `aggregateRating`), `ComparisonTable`, `VideoObject` nếu có video.
27. **FAQPage khớp 100% nguyên văn:** Câu hỏi/đáp trong Schema phải giống hệt trong bài, Google check từng ký tự.
28. **Speakable / AI Summary:** Thêm trường `speakable` và `abstract` cho AI đọc.
29. **Citation & Source:** Thêm `citation` trong Schema trỏ về Sony official. Tool mới `citation_checker` tự kiểm tra link sống/chết.
30. **Author E-E-A-T:** Schema `Person` có `sameAs` link tới Facebook/Instagram/LinkedIn của tác giả, có `knowsAbout: ["Sony Alpha", "Wedding Photography"]`.
31. **Entity linking:** Tự động link lần đầu nhắc "Eye AF" tới trang giải thích Eye AF trong glossary của bạn (internal entity graph).
32. **AIO Score:** Tool mới `aio_audit` chấm điểm riêng cho AI Overviews (0-100), khác với `seo_audit`. Báo "Khả năng được AI Overviews trích: 78%".
33. **Zero-click optimization:** Viết 1 đoạn "Key Takeaways" dạng bullet 3-5 ý ở cuối, để AI copy thẳng.
34. **Multimodal:** Ảnh phải có `ImageObject` schema với `caption` mô tả chi tiết, để Gemini/ChatGPT Vision hiểu.
35. **Bản tiếng Anh song song (tùy chọn):** Nếu có bản EN tóm tắt 200 từ ở cuối, Perplexity dễ trích hơn cho user quốc tế.

### Tool mới đề xuất (đã thêm vào roadmap MCP)

| Tool mới | Việc làm |
| :--- | :--- |
| `aio_audit` | Chấm 15 tiêu chí AIO Core + 10 Schema, trả về % được trích |
| `paa_generator` | Gợi ý 10 câu PAA từ Google/Perplexity cho từ khóa |
| `entity_extractor` | Trích entity (model máy, thông số) để đảm bảo đủ |
| `citation_checker` | Kiểm tra link nguồn sống/chết, có phải nguồn uy tín không |
| `freshness_check` | Báo bài này cũ bao lâu, gợi ý cập nhật giá/thông số |
| `speakable_generator` | Sinh đoạn tóm tắt 30s cho Google Assistant đọc |

---

## Cách dùng 3 chế độ

### A: Dịch menu
```
Dịch 3 chuỗi này cho A7 IV: Focus Area, Silent Shooting, Anti-flicker Shoot Sel.
```
→ Trả về bảng + % khung + gợi ý rút gọn nếu tràn.

Với file Excel:
```
Rà file ~/Downloads/ILDC_TranslationCheck_VN.xls, chỉ lấy dòng lỗi, xuất ra ~/Desktop/fixed.xls
```

### B: Dịch tài liệu
```
Dịch file ~/a7iv-help-guide.pdf sang tiếng Việt tự nhiên, giữ heading, tên menu in đậm **Vùng lấy nét** (Focus Area)
```

### C: Viết blog AIO-first (MỚI)
```
Viết blog 1500 từ "Sony A7 IV hay A7R V cho thợ cưới", từ khóa "Sony A7 IV hay A7R V", độc giả thợ cưới HCM, yêu cầu AIO-first
```

AI sẽ:
1. Gọi `paa_generator` lấy 10 câu hỏi PAA
2. Viết outline có TL;DR, bảng so sánh, FAQ, Key Takeaways
3. Gọi `entity_extractor` đảm bảo đủ thông số
4. Gọi `style_lint` bỏ văn AI-sounding
5. Gọi `seo_audit` + `aio_audit` → Bảng `Mục | Kết quả | Bằng chứng | Cách sửa` + điểm AIO Score
6. Gọi `faq_schema` + `product_schema` sinh JSON-LD

---

## Quy tắc thuật ngữ (giữ nguyên)

| EN | Menu (ngắn) | Bài viết (quen) |
| Full Frame | Toàn khung | full-frame |
| Eye AF | Eye AF | lấy nét mắt (Eye AF) |
| Image Stabilization | Ổn định hình ảnh | chống rung IBIS |

Giữ tiếng Anh: Zoom, Time Code, Preset...

---

## Lộ trình cải tiến SEO/AIO đã cập nhật

- [x] v1.0.0: Fix plugin.json + marketplace + CI
- [x] v1.1.0: Rewrite README end-user + checklist 35 tiêu chí AIO-first
- [x] v1.2.0: Thêm 5 tool mới (`aio_audit`, `paa_generator`, `citation_checker`, `freshness_check`, `brand_voice_checker`) vào MCP + test CI
- [ ] v1.3.0: Thêm Schema Product/HowTo/VideoObject, tự sinh Speakable
- [ ] v1.4.0: Tích hợp Obsidian AIO dashboard: xem bài nào AIO Score thấp

---

## FAQ

**AIO khác SEO thế nào?**
SEO là để lên top Google. AIO là để được AI trả lời thay bạn. Năm 2026, người dùng hỏi ChatGPT trước, Google sau. Nếu bài bạn không có TL;DR, FAQ tự đứng, bảng so sánh, AI sẽ không trích.

**Làm sao biết bài có được AI trích không?**
Dùng `aio_audit`. Nếu TL;DR thiếu, FAQ trả lời kiểu "xem ở trên", không có bảng, điểm sẽ <50% và báo "AI sẽ bỏ qua".

**Tôi chỉ viết blog, có cần MCP không?**
Có. `aio_audit` và `citation_checker` chỉ chạy được với MCP, nó đếm ký tự, check link thật, không phải đoán.

---

**Bắt đầu ngay:**
> Dịch Focus Area, Silent Shooting sang tiếng Việt cho A7 IV và viết TL;DR 50 từ để AI Overviews trích
