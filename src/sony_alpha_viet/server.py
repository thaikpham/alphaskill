"""MCP server: Sony Alpha Vietnamese menu translator + blog audit."""
from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import core, memory, blog
from .paths import DATA, ensure_data_dir
from .core import Store

# Ensure data dir on first run
ensure_data_dir()

mcp = FastMCP("sony-alpha-viet", instructions=(
    "Sony Alpha máy ảnh dịch menu sang tiếng Việt + hỗ trợ viết blog/tài liệu. "
    "\n\n"
    "**Quy trình A: Menu (OSD)**: get_guidelines → prepare_batch (tra bộ nhớ dịch + thuật ngữ) → dịch "
    "→ check_translation cho từng chuỗi → sửa đến khi ok. "
    "Khi người dùng duyệt hoặc sửa: gọi record_term / record_feedback / remember_translation để ghi nhớ; "
    "cuối phiên gọi learn rồi commit_memory. "
    "Ngoại lệ: thuật ngữ tiếng Anh (Zoom, Time Code, Preset) mà tiếng Việt không giúp → dùng keep_english. "
    "\n\n"
    "**Quy trình B: Blog/Tài liệu**: lookup_prose_term (tra thuật ngữ chuẩn từ glossary) → viết theo template "
    "→ style_lint (kiểm tra VAI-sounding, bị động, độ dài câu) → seo_audit (kiểm tra 21 mục SEO/AIO) "
    "→ faq_schema (tạo JSON-LD Article+FAQPage). Nếu MCP không có, thực hiện kiểm tra thủ công từ checklist."))
store = Store()


def _layout(max_width, font_w, font_h, rows, linefeed):
    if not max_width:
        return None
    return {"max_w": max_width, "font_w": font_w or 27, "font_h": font_h or 36, "rows": rows or 1, "linefeed": linefeed or "Off"}


@mcp.tool()
def get_guidelines(section: str = "all") -> str:
    """Quy tắc dịch, ngoại lệ giữ tiếng Anh và các thuật ngữ đã khóa. section: all | rules | exceptions | locked_terms | keep_english | learning_log."""
    parts = []
    if section in ("all", "rules"):
        parts.append((DATA / "rules.md").read_text(encoding="utf-8"))
    if section in ("all", "exceptions"):
        parts.append("## Ngoại lệ giữ nguyên tiếng Anh\n" + json.dumps(store.exceptions, ensure_ascii=False, indent=1))
    if section in ("all", "locked_terms"):
        locked = [f"- {g['en']} = {g['vi']}" + (f" (ngắn: {g['short']})" if g.get('short') and g['short'] != g['vi'] else "") +
                  (f" — {g['note']}" if g.get("note") else "") for g in store.glossary if g.get("locked")]
        parts.append("## Thuật ngữ đã khóa (ưu tiên cao nhất)\n" + "\n".join(locked))
    if section in ("all", "keep_english"):
        ke_list = [f"- {k['term']}: {', '.join(k.get('vi_variants', {}).keys())}" + (f" — {k['why']}" if k.get('why') else "") for k in store.keep]
        parts.append("## Thuật ngữ giữ tiếng Anh (keep_english)\n" + ("\n".join(ke_list) if ke_list else "Trống"))
    if section in ("all", "learning_log") and (DATA / "LEARNING_LOG.md").exists():
        parts.append((DATA / "LEARNING_LOG.md").read_text(encoding="utf-8")[-4000:])
    return "\n\n".join(parts)


@mcp.tool()
def lookup_term(text: str, limit: int = 20) -> list[dict]:
    """Thuật ngữ trong glossary xuất hiện trong chuỗi tiếng Anh (hoặc gần đúng với từ cần tra)."""
    return core.lookup_terms(store, text, limit)


@mcp.tool()
def search_memory(text: str, limit: int = 5, min_score: float = 0.55) -> list[dict]:
    """Tìm bản dịch đã duyệt gần giống trong bộ nhớ dịch (8.346 chuỗi ILDC Rev.3 + mọi bản người dùng duyệt sau này)."""
    return core.search_tm(store, text, limit, min_score)


@mcp.tool()
def prepare_batch(items: list[dict]) -> list[dict]:
    """Chuẩn bị dịch hàng loạt. items: [{id?, en, max_width?, font_w?, font_h?, rows?, linefeed?}].
    Trả về cho mỗi chuỗi: bản khớp trong bộ nhớ, thuật ngữ liên quan, gợi ý từ quy tắc nếu có bản khớp 100%."""
    out = []
    for it in items:
        en = it["en"]
        tm = core.search_tm(store, en, 3)
        terms = core.lookup_terms(store, en, 12)
        exact = next((m for m in tm if m["score"] >= 0.999), None)
        out.append({"id": it.get("id"), "en": en, "exact_match": exact["vi"] if exact else None,
                    "memory": tm, "terms": [{"en": g["en"], "vi": g["vi"], "short": g.get("short"), "locked": g.get("locked"), "note": g.get("note")} for g in terms]})
    return out


@mcp.tool()
def check_translation(en: str, vi: str, max_width: int = 0, font_w: int = 0, font_h: int = 0, rows: int = 1,
                      linefeed: str = "Off", autofix: bool = True) -> dict:
    """Kiểm tra bản dịch: tiếng Anh sót, từ bị cấm, viết tắt rụng chữ, biến/icon, thống nhất với bộ nhớ, độ rộng OSD.
    autofix=True: áp quy tắc tự động trước rồi kiểm tra lại, trả về bản đã sửa."""
    lay = _layout(max_width, font_w, font_h, rows, linefeed)
    fixed = core.apply_rules(store, vi, en, lay) if autofix else {"text": vi, "changed": False, "applied": []}
    res = core.audit(store, en, fixed["text"], lay)
    res.update({"text": fixed["text"], "autofixed": fixed["changed"], "rules_applied": fixed["applied"]})
    # Add short_candidates when fit is BORDER/OVER
    if lay and res.get("fit", {}).get("verdict") in ("BORDER", "OVER"):
        res["short_candidates"] = core.suggest_short(store, en, fixed["text"], lay, limit=5)
    return res


@mcp.tool()
def check_fit(text: str, max_width: int, font_w: int = 27, font_h: int = 36, rows: int = 1, linefeed: str = "Off") -> dict:
    """Ước lượng độ rộng hiển thị OSD. OK ≤92%, BORDER 93–100% (cần SonyTool xác nhận), OVER = vượt."""
    return core.fit(text, max_width, font_w, font_h, rows, linefeed)


@mcp.tool()
def keep_english(term: str, vi_variants: dict, en_pattern: str = "", why: str = "", apply: bool = False) -> dict:
    """Quản lý thuật ngữ giữ tiếng Anh: khi tiếng Việt không giúp người dùng.
    vi_variants: từ điển {biến_việt: mẫu_thay_thế} — dùng {term} cho thuật ngữ.
    apply=False: xem trước kế hoạch; apply=True: thực hiện và lưu tất cả tệp."""
    return memory.keep_english(store, term, vi_variants, en_pattern, why, apply)


@mcp.tool()
def suggest_short(en: str, vi: str, max_width: int = 0, font_w: int = 0, font_h: int = 0, rows: int = 1, linefeed: str = "Off", limit: int = 5) -> list[dict]:
    """Gợi ý bản dịch ngắn hơn khi OSD tràn khung. Trả về danh sách {text, fit, source} sắp xếp theo fit verdict."""
    lay = _layout(max_width, font_w, font_h, rows, linefeed)
    return core.suggest_short(store, en, vi, lay, limit)


@mcp.tool()
def record_term(en: str, vi: str, short: str = "", note: str = "", locked: bool = True) -> dict:
    """Ghi nhớ quyết định thuật ngữ của người dùng (ví dụ Shutter Button = nút chụp). Thuật ngữ khóa luôn được ưu tiên."""
    return memory.record_term(store, en, vi, short, note, locked)


@mcp.tool()
def record_feedback(en: str, wrong: str, right: str, reason: str = "", project: str = "", always: bool = False,
                    max_width: int = 0, font_w: int = 0, font_h: int = 0, rows: int = 1, linefeed: str = "Off") -> dict:
    """Ghi nhớ một lần người dùng sửa bản dịch. Cập nhật bộ nhớ dịch; cụm từ bị sửa ≥2 lần (hoặc always=True) tự thành quy tắc."""
    return memory.record_feedback(store, en, wrong, right, reason, project, always, _layout(max_width, font_w, font_h, rows, linefeed))


@mcp.tool()
def remember_translation(en: str, vi: str, project: str = "") -> dict:
    """Lưu một cặp EN→VI đã được người dùng duyệt vào bộ nhớ dịch."""
    return memory.remember_translation(store, en, vi, project)


@mcp.tool()
def ban_term(pattern: str, why: str) -> dict:
    """Thêm mẫu (regex) bị cấm trong bản dịch, ví dụ 'nút màn trập'."""
    return memory.ban_term(store, pattern, why)


@mcp.tool()
def learn(min_count: int = 2, dry_run: bool = False) -> dict:
    """Tự cải tiến: biến các lần sửa lặp lại thành quy tắc thay thế. dry_run=True chỉ xem trước."""
    return memory.learn(store, min_count, dry_run)


@mcp.tool()
def review_memory() -> dict:
    """Tự rà soát bộ nhớ: quy tắc học được nhưng chưa dùng, thuật ngữ mâu thuẫn, thuật ngữ khóa dính mẫu bị cấm."""
    return memory.review_rules(store)


@mcp.tool()
def disable_rule(rule_id: str, why: str = "") -> dict:
    """Tắt một quy tắc thay thế sai (giữ lại trong lịch sử)."""
    return memory.disable_rule(store, rule_id, why)


@mcp.tool()
def commit_memory(message: str = "Cập nhật bộ nhớ dịch") -> dict:
    """Commit thư mục data/ vào git để mọi thay đổi bộ nhớ có lịch sử và hoàn tác được."""
    store.save_rules()  # persist hit counters
    return memory.commit_memory(message)


@mcp.tool()
def xls_read(path: str, only_flagged: bool = False, limit: int = 0) -> dict:
    """Đọc file Sony *_VN.xls (sheet VN): S#, EN, bản dịch hiện tại, AN/AU/AV, layout. only_flagged=True chỉ trả dòng vi phạm quy tắc."""
    from .xls import sonyxls
    rows = sonyxls.read_rows(path)
    out = []
    for r in rows:
        eff = r["an"] or r["vi"]
        if only_flagged:
            a = core.audit(store, r["en"], eff, r["layout"])
            if a["ok"]:
                continue
            r["issues"] = a["issues"]; r["fit"] = a.get("fit")
        out.append(r)
        if limit and len(out) >= limit:
            break
    return {"total": len(rows), "returned": len(out), "rows": out}


@mcp.tool()
def xls_write(src: str, out: str, proposals: list[dict]) -> dict:
    """Ghi đề xuất vào bản sao file xls (chỉ AN/AU/AV, giữ nguyên byte phần còn lại). proposals: [{row, sid, an, au, av}].
    AU phải thuộc danh sách dropdown của Sony; AV là lý do bằng tiếng Anh. Không bao giờ ghi đè file gốc."""
    from .xls import sonyxls
    return sonyxls.write_proposals(src, out, proposals)


# === Blog tools ===

@mcp.tool()
def slugify(text: str, max_words: int = 6) -> str:
    """Chuyển tiếng Việt → ASCII slug (đ→d, loại dấu, dấu gạch nối). max_words tối đa số từ (mặc định 6)."""
    return blog.slugify(text, max_words)


@mcp.tool()
def count_words(text: str) -> int:
    """Đếm từ trong markdown (loại table, code fence, frontmatter)."""
    return blog.count_words(text)


@mcp.tool()
def lookup_prose_term(query: str) -> list[dict]:
    """Tra cứu thuật ngữ trong glossary (EN/JP/Menu/Bài viết) — fuzzy match substring, case-insensitive."""
    return blog.lookup_prose_term(query)


@mcp.tool()
def style_lint(text: str) -> dict:
    """Kiểm tra văn phong: cụm AI-sounding, bị động, độ dài câu, "của" lặp, từ đôi, thập phân prose."""
    return blog.style_lint(text)


@mcp.tool()
def seo_audit(markdown: str, primary_keyword: str = "", secondary_keywords: list[str] = None) -> dict:
    """SEO + AIO audit: kiểm tra 21 mục máy được từ seo-aio-checklist.md. Trả về score, failed items, chi tiết."""
    if secondary_keywords is None:
        secondary_keywords = []
    return blog.seo_audit(markdown, primary_keyword, secondary_keywords)


@mcp.tool()
def faq_schema(markdown: str, url: str = "", site_name: str = "", image: str = "") -> str:
    """Tạo JSON-LD Article + FAQPage từ markdown frontmatter + FAQ section."""
    return blog.faq_schema(markdown, url, site_name, image)


@mcp.tool()
def data_info() -> dict:
    """Thông tin về thư mục dữ liệu: đường dẫn, tính chất (sample hay thực), số lượng từng loại."""
    glossary_count = len(store.glossary)
    tm_count = len(store.tm)
    rules_count = len(store.rules.get("substitutions", []))
    keep_count = len(store.keep)

    is_sample = not (DATA / "LEARNING_LOG.md").exists() and len(store.tm) == 0

    return {
        "data_path": str(DATA),
        "is_sample_data": is_sample,
        "glossary_count": glossary_count,
        "tm_count": tm_count,
        "rules_count": rules_count,
        "keep_english_count": keep_count
    }


# === Resources ===

def _get_skill_root() -> Path:
    """Locate skill dir relative to package root."""
    return Path(__file__).resolve().parents[2] / "skills" / "sony-alpha-viet"

@mcp.resource("sony-alpha-viet://references/{name}")
def reference_resource(name: str) -> str:
    """Skill reference files (glossary-vi, writing-style-vi, seo-aio-checklist, etc)."""
    ref_file = _get_skill_root() / "references" / name
    if ref_file.exists():
        return ref_file.read_text(encoding="utf-8")
    return ""

@mcp.resource("sony-alpha-viet://templates/{name}")
def template_resource(name: str) -> str:
    """Skill templates (blog-post-template, faq-schema)."""
    tpl_file = _get_skill_root() / "templates" / name
    if tpl_file.exists():
        return tpl_file.read_text(encoding="utf-8")
    return ""


# === Prompts ===

@mcp.prompt("translate_menu")
def prompt_translate_menu(model: str = "Claude", source_lang: str = "English", strings: str = "") -> str:
    """Hướng dẫn dịch menu Sony: get_guidelines → prepare_batch → dịch."""
    return f"""Dịch menu máy ảnh Sony từ {source_lang} sang tiếng Việt thuần Việt.

**Danh sách chuỗi cần dịch:**
{strings}

**Quy trình:**
1. Gọi `mcp__sony-alpha-viet__get_guidelines()` để đọc quy tắc dịch
2. Gọi `mcp__sony-alpha-viet__prepare_batch([{{"en": "Aperture", ...}}, ...])` để tra bộ nhớ và thuật ngữ
3. Dịch từng chuỗi, sử dụng đề xuất từ `prepare_batch`
4. Gọi `mcp__sony-alpha-viet__check_translation(en, vi)` để kiểm tra từng bản dịch
5. Nếu sai, sửa và kiểm tra lại
6. Khi ok, gọi `mcp__sony-alpha-viet__remember_translation(en, vi)` để lưu
7. Cuối phiên: `mcp__sony-alpha-viet__learn()` rồi `mcp__sony-alpha-viet__commit_memory()`"""

@mcp.prompt("write_blog")
def prompt_write_blog(topic: str = "", primary_keyword: str = "", audience: str = "",
                      models: str = "", length: str = "") -> str:
    """Hướng dẫn viết blog Sony: template → style_lint → seo_audit → faq_schema."""
    return f"""Viết bài blog tiếng Việt về máy ảnh Sony.

**Chủ đề:** {topic}
**Từ khóa chính:** {primary_keyword}
**Độc giả:** {audience}
**Mô hình gợi ý:** {models}
**Độ dài:** {length}

**Quy trình:**
1. Gọi `mcp__sony-alpha-viet__reference("glossary-vi.md")` để xem danh sách thuật ngữ chuẩn
2. Dùng template từ `mcp__sony-alpha-viet__template("blog-post-template.md")`
3. Viết bài, sử dụng `mcp__sony-alpha-viet__lookup_prose_term(word)` để xác minh thuật ngữ
4. Gọi `mcp__sony-alpha-viet__style_lint(bài)` để kiểm tra văn phong (tránh AI-sounding, bị động, v.v.)
5. Gọi `mcp__sony-alpha-viet__seo_audit(bài, primary_keyword)` để kiểm tra 21 mục SEO/AIO
6. Sửa cho đến khi audit xanh
7. Gọi `mcp__sony-alpha-viet__faq_schema(bài)` để tạo JSON-LD schema

**Cấu trúc bài:**
- Frontmatter: meta_title (50–60 ký tự), meta_description (140–160), slug, primary_keyword, author, updated (DD/MM/YYYY), schema
- H1: tiêu đề chính (có chứa primary_keyword)
- TL;DR: 40–70 từ
- H2/H3: cấu trúc câu hỏi
- Bảng/checklist/danh sách
- FAQ: 3–6 câu, mỗi trả lời 40–70 từ
- JSON-LD script: Article + FAQPage"""

@mcp.prompt("audit_post")
def prompt_audit_post(path_or_text: str = "") -> str:
    """Hướng dẫn audit bài blog hiện có: đọc → style_lint → seo_audit → sửa."""
    return f"""Audit bài blog/tài liệu Sony hiện có.

**Đường dẫn hoặc nội dung:**
{path_or_text}

**Quy trình:**
1. Đọc bài (nếu là đường dẫn, mở file)
2. Gọi `mcp__sony-alpha-viet__style_lint(bài)` → xem danh sách issue văn phong
3. Gọi `mcp__sony-alpha-viet__seo_audit(bài, primary_keyword)` → xem score, mục failed
4. Sửa từng issue:
   - Văn phong: loại AI-sounding, thay bị động, tách câu dài, etc.
   - SEO: thêm từ khóa, sửa meta title/description, thêm link, v.v.
5. Lặp lại audit cho đến khi style ✓, seo score ≥90%, mục bắt buộc xanh
6. Gọi `mcp__sony-alpha-viet__faq_schema(bài)` để sinh schema JSON-LD nếu chưa có

**Checklist item quan trọng:**
- #1: Từ khóa ở H1, slug, 100w, H2, meta_description
- #6: TL;DR 40–70 từ
- #8: Bảng/checklist/danh sách
- #11: FAQ 3–6 câu, 40–70 từ
- #15: Không [cần xác minh]
- #19: JSON-LD Article + FAQPage hợp lệ"""


def main():
    mcp.run()


if __name__ == "__main__":
    main()
