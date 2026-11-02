# sony-alpha-viet — Claude Code skill

Dịch và biên tập tiếng Việt cho menu/tài liệu Sony Alpha (nguồn Anh hoặc Nhật), viết và audit blog tiếng Việt tối ưu SEO + AIO, chuẩn hóa thuật ngữ nhiếp ảnh.

| Chế độ | Dùng cho | Đầu ra |
|---|---|---|
| A. Menu OSD | Chuỗi menu, thông báo, help text, file `*_TranslationCheck_VN.xls` | Bảng Markdown + CSV |
| B. Tài liệu | Hướng dẫn sử dụng, help guide, PDF/DOCX/URL | Markdown giữ cấu trúc |
| C. Blog SEO + AIO | Viết, biên tập, audit bài blog | Markdown + meta + JSON-LD + bảng audit |

## Cài đặt

```bash
git clone https://github.com/thaikpham/thaikpham-blogskill.git ~/.claude/skills/sony-alpha-viet
```

Gọi trong Claude Code: `/sony-alpha-viet`, hoặc nói "dịch menu Sony…", "viết blog Sony Alpha…", "audit SEO AIO bài này…".

Chế độ A dùng MCP server `sony-vn-translator` (bộ nhớ dịch, thuật ngữ khóa, kiểm độ rộng OSD). Không có MCP, skill vẫn chạy với `references/glossary-vi.md` và ghi rõ "chưa kiểm bằng MCP".

## Cấu trúc

```
SKILL.md
references/  glossary-vi.md · sony-menu-terms.md · seo-aio-checklist.md · writing-style-vi.md
templates/   blog-post-template.md · menu-translation-table.csv · faq-schema.json
examples/    example-menu-translation.md · example-blog-post.md
```

## Giới hạn

Skill chỉ dịch và chuẩn hóa text. Không sửa, đóng gói hay flash firmware; không bật service mode.
