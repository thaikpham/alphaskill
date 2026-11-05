"""MCP server: Sony Alpha Vietnamese menu translator + blog audit."""
from __future__ import annotations

import functools
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import core, memory, blog
from . import obsidian, paths
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
    "**Quy trình B: Blog/Tài liệu (AIO-first 2026)**: lookup_prose_term (tra thuật ngữ chuẩn từ glossary) "
    "→ paa_generator (10 câu PAA) → viết theo template → style_lint (cụm AI-sounding, bị động, câu dài, thuật ngữ) "
    "→ seo_audit (SEO foundation) → aio_audit (chấm AIO-first 35 tiêu chí) → citation_checker (check link Tier 1) "
    "→ freshness_check (kiểm tra độ mới 11/2026) → brand_voice_checker (bảo vệ Sony, sensor #1, ngàm E, KANDO) "
    "→ faq_schema (tạo JSON-LD Article+FAQPage). Nếu MCP không có, thực hiện kiểm tra thủ công từ checklist."))
store = Store()


def tool(fn):
    """mcp.tool() that first picks up changes made by other processes, so a stale in-memory copy never overwrites them."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        store.refresh()
        try:
            return fn(*args, **kwargs)
        finally:
            store.mark_current()
    return mcp.tool()(wrapper)


def _layout(max_width, font_w, font_h, rows, linefeed):
    if not max_width:
        return None
    return {"max_w": max_width, "font_w": font_w or 27, "font_h": font_h or 36, "rows": rows or 1, "linefeed": linefeed or "Off"}


@tool
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


@tool
def lookup_term(text: str, limit: int = 20) -> list[dict]:
    """Thuật ngữ trong glossary xuất hiện trong chuỗi tiếng Anh (hoặc gần đúng với từ cần tra)."""
    return core.lookup_terms(store, text, limit)


@tool
def search_memory(text: str, limit: int = 5, min_score: float = 0.55) -> list[dict]:
    """Tìm bản dịch đã duyệt gần giống trong bộ nhớ dịch (8.346 chuỗi ILDC Rev.3 + mọi bản người dùng duyệt sau này)."""
    return core.search_tm(store, text, limit, min_score)


@tool
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


@tool
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


@tool
def check_fit(text: str, max_width: int, font_w: int = 27, font_h: int = 36, rows: int = 1, linefeed: str = "Off") -> dict:
    """Ước lượng độ rộng hiển thị OSD. OK ≤92%, BORDER 93–100% (cần SonyTool xác nhận), OVER = vượt."""
    return core.fit(text, max_width, font_w, font_h, rows, linefeed)


@tool
def keep_english(term: str, vi_variants: dict, en_pattern: str = "", why: str = "", apply: bool = False) -> dict:
    """Quản lý thuật ngữ giữ tiếng Anh: khi tiếng Việt không giúp người dùng.
    vi_variants: từ điển {biến_việt: mẫu_thay_thế} — dùng {term} cho thuật ngữ.
    apply=False: xem trước kế hoạch; apply=True: thực hiện và lưu tất cả tệp."""
    return memory.keep_english(store, term, vi_variants, en_pattern, why, apply)


@tool
def suggest_short(en: str, vi: str, max_width: int = 0, font_w: int = 0, font_h: int = 0, rows: int = 1, linefeed: str = "Off", limit: int = 5) -> list[dict]:
    """Gợi ý bản dịch ngắn hơn khi OSD tràn khung. Trả về danh sách {text, fit, source} sắp xếp theo fit verdict."""
    lay = _layout(max_width, font_w, font_h, rows, linefeed)
    return core.suggest_short(store, en, vi, lay, limit)


@tool
def record_term(en: str, vi: str, short: str = "", note: str = "", locked: bool = True) -> dict:
    """Ghi nhớ quyết định thuật ngữ của người dùng (ví dụ Shutter Button = nút chụp). Thuật ngữ khóa luôn được ưu tiên."""
    return memory.record_term(store, en, vi, short, note, locked)


@tool
def record_feedback(en: str, wrong: str, right: str, reason: str = "", project: str = "", always: bool = False,
                    max_width: int = 0, font_w: int = 0, font_h: int = 0, rows: int = 1, linefeed: str = "Off") -> dict:
    """Ghi nhớ một lần người dùng sửa bản dịch. Cập nhật bộ nhớ dịch; always=True tự thành quy tắc; các lần sửa lặp lại chờ bạn gọi learn (dry_run=True để xem trước)."""
    return memory.record_feedback(store, en, wrong, right, reason, project, always, _layout(max_width, font_w, font_h, rows, linefeed))


@tool
def remember_translation(en: str, vi: str, project: str = "", tm_id: str = "") -> dict:
    """Lưu một cặp EN→VI đã được người dùng duyệt vào bộ nhớ dịch. Chuỗi chỉ khác icon đầu dòng giữ icon của chính nó;
    chuỗi khác token ở giữa không bị đụng. tm_id (S#) để ghi đúng một dòng."""
    return memory.remember_translation(store, en, vi, project, tm_id=tm_id)


@tool
def ban_term(pattern: str, why: str) -> dict:
    """Thêm mẫu (regex) bị cấm trong bản dịch, ví dụ 'nút màn trập'."""
    return memory.ban_term(store, pattern, why)


@tool
def learn(min_count: int = 2, dry_run: bool = False) -> dict:
    """Tự cải tiến: biến các lần sửa lặp lại (≥min_count) thành quy tắc thay thế. dry_run=True chỉ xem trước không commit."""
    return memory.learn(store, min_count, dry_run)


@tool
def review_memory() -> dict:
    """Tự rà soát bộ nhớ: quy tắc học được nhưng chưa dùng, thuật ngữ mâu thuẫn, thuật ngữ khóa dính mẫu bị cấm."""
    return memory.review_rules(store)


@tool
def disable_rule(rule_id: str, why: str = "") -> dict:
    """Tắt một quy tắc thay thế sai (giữ lại trong lịch sử)."""
    return memory.disable_rule(store, rule_id, why)


@tool
def commit_memory(message: str = "Cập nhật bộ nhớ dịch") -> dict:
    """Commit thư mục data/ vào git để mọi thay đổi bộ nhớ có lịch sử và hoàn tác được."""
    store.save_rules()  # persist hit counters
    return memory.commit_memory(message)


@tool
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


@tool
def xls_write(src: str, out: str, proposals: list[dict], overwrite: bool = False) -> dict:
    """Ghi đề xuất vào bản sao file xls (chỉ AN/AU/AV, giữ nguyên byte phần còn lại). proposals: [{row, sid, an, au, av}].
    AU phải thuộc danh sách dropdown của Sony; AV là lý do bằng tiếng Anh. Không bao giờ ghi đè file gốc.
    overwrite=True: sửa lại ô AN/AU/AV đã có giá trị (rà soát lần 2); mặc định chỉ điền ô trống."""
    from .xls import sonyxls
    return sonyxls.write_proposals(src, out, proposals, overwrite)


@tool
def xls_review(folder: str, out_csv: str = "") -> dict:
    """Rà soát cả thư mục *TranslationCheck_VN.xls (chấm AN nếu có, không thì VI; kiểm lại cả chuỗi đã duyệt):
    lỗi quy tắc, tràn khung, thuật ngữ khóa, lệch bộ nhớ, cùng chuỗi gốc mà chọn từ khác dù vừa khung.
    Trả về {files, rows, counts, by_file, top}; out_csv → ghi toàn bộ phát hiện ra CSV."""
    from . import review
    return review.review_folder(folder, out_csv)


# === Blog tools ===

@tool
def slugify(text: str, max_words: int = 6) -> str:
    """Chuyển tiếng Việt → ASCII slug (đ→d, loại dấu, dấu gạch nối). max_words tối đa số từ (mặc định 6)."""
    return blog.slugify(text, max_words)


@tool
def count_words(text: str) -> int:
    """Đếm từ trong markdown (loại table, code fence, frontmatter)."""
    return blog.count_words(text)


@tool
def lookup_prose_term(query: str) -> list[dict]:
    """Tra cứu thuật ngữ trong glossary (EN/JP/Menu/Bài viết) — fuzzy match substring, case-insensitive."""
    return blog.lookup_prose_term(query)


@tool
def style_lint(text: str) -> dict:
    """Kiểm tra văn phong: cụm AI-sounding, bị động, độ dài câu, "của" lặp, từ đôi, thập phân prose."""
    return blog.style_lint(text)


@tool
def seo_audit(markdown: str, primary_keyword: str = "", secondary_keywords: list[str] = None) -> dict:
    """SEO + AIO audit: kiểm tra 21 mục máy được từ seo-aio-checklist.md. Trả về score, failed items, chi tiết."""
    if secondary_keywords is None:
        secondary_keywords = []
    return blog.seo_audit(markdown, primary_keyword, secondary_keywords)


@tool
def faq_schema(markdown: str, url: str = "", site_name: str = "", image: str = "") -> str:
    """Tạo JSON-LD Article + FAQPage từ markdown frontmatter + FAQ section."""
    return blog.faq_schema(markdown, url, site_name, image)


@tool
def aio_audit(text: str, primary_keyword: str = "") -> dict:
    """Chấm điểm AIO-first 35 tiêu chí cho bài blog Sony Alpha tiếng Việt (AIO > SEO 2026).
    Trả về aio_score (0-100), verdict (khả năng AI Overviews/ChatGPT trích), và bảng chi tiết."""
    return blog.aio_audit(text, primary_keyword)


@tool
def paa_generator(primary_keyword: str, audience: str = "thợ chụp cưới", models: list[str] = None) -> dict:
    """Gợi ý 10 câu People Also Ask (PAA) cho từ khóa Sony Alpha kèm gợi ý trả lời tự đứng 40-70 từ."""
    return blog.paa_generator(primary_keyword, audience, models)


@tool
def citation_checker(text: str) -> dict:
    """Kiểm tra nguồn trích dẫn cho bài blog: link Tier 1 Sony official, Tier 2 uy tín, kiểm tra link sống/chết."""
    return blog.citation_checker(text)


@tool
def freshness_check(text: str) -> dict:
    """Kiểm tra độ mới của bài, phát hiện giá cũ/firmware cũ, gợi ý cập nhật 11/2026."""
    return blog.freshness_check(text)


@tool
def brand_voice_checker(text: str) -> dict:
    """Kiểm tra nguyên tắc bảo vệ Sony: sensor số 1 TG, ngàm E >200 lens, KANDO/cân bằng, không chê Sony, kết bài KANDO."""
    return blog.brand_voice_checker(text)


@tool
def data_info() -> dict:
    """Thông tin về thư mục dữ liệu: đường dẫn, tính chất (sample hay thực), số lượng từng loại."""
    glossary_count = len(store.glossary)
    tm_count = len(store.tm)
    rules_count = len(store.rules.get("substitutions", []))
    keep_count = len(store.keep)

    is_sample = not (DATA / "LEARNING_LOG.md").exists() and len(store.tm) == 0

    return {
        "data_path": str(DATA),
        "data_source": paths.DATA_SOURCE,
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


@tool
def consistency_report(limit: int = 50) -> list[dict]:
    """Các chuỗi tiếng Anh đang có nhiều bản dịch khác nhau trong bộ nhớ (bỏ qua khác biệt icon), nhóm lớn trước."""
    from . import obsidian
    return obsidian.consistency_report(store, limit)


@tool
def obsidian_export() -> dict:
    """Ghi/cập nhật vault Obsidian (cấu hình trong ~/.config/sony-alpha-viet/config.json) theo cây đánh số: 1 Kiến thức,
    2 Giáo án (bản sao kho kiến thức), 3 Thuật ngữ, 4 Dịch menu, 5 Tài liệu Sony, 6 Blog, 9 Skill; tự chuyển note từ bố cục cũ.
    Note người dùng đang sửa dở (thuật ngữ, kiến thức) không bị ghi đè: xem skipped_pending_edits, knowledge.pending_edits."""
    from . import obsidian
    return obsidian.export(store)


@tool
def obsidian_import(apply: bool = False) -> dict:
    """Đưa thay đổi trong Obsidian về kho dữ liệu: note thuật ngữ (3 Thuật ngữ/, ghi bằng record_term) và note kiến thức/giáo án
    sửa hoặc tạo mới (1 Kiến thức/, 2 Giáo án/). apply=False chỉ xem trước."""
    from . import obsidian
    return obsidian.import_all(store, apply)


@tool
def obsidian_audit_note(path: str, primary_keyword: str = "") -> dict:
    """Chấm SEO/AIO một bản nháp trong vault (đường dẫn tương đối với thư mục skill trong vault, ví dụ Blog/ten-bai.md,
    hoặc tuyệt đối). Ghi note '<tên> — SEO audit' bên cạnh và thuộc tính seo_score/seo_complete/seo_audited vào bản nháp."""
    from . import obsidian
    return obsidian.audit_note(path, primary_keyword)


@tool
def ingest_docs(folder: str) -> dict:
    """Nạp tài liệu Sony (PDF Hướng dẫn khởi động/Help Guide, DOCX chứa link) từ một thư mục vào dữ liệu riêng (DATA/docs).
    Tự chuyển font VNI cũ sang Unicode, bỏ file trùng. Không đưa tài liệu lên repo công khai."""
    from . import docs
    return docs.ingest(folder)


@tool
def search_docs(query: str, limit: int = 10) -> list[dict]:
    """Tìm cụm từ trong tài liệu tiếng Việt chính thức của Sony (theo model, trang). Dùng để xem Sony Việt Nam diễn đạt thế nào
    trước khi đề xuất thuật ngữ mới hoặc khi dịch tài liệu."""
    from . import docs
    return docs.search(query, limit)


@tool
def docs_term_report() -> dict:
    """Đối chiếu glossary/quy tắc với tài liệu Sony: thuật ngữ khóa Sony có dùng, từ bị cấm mà Sony vẫn dùng (theo model),
    từ tiếng Anh Sony giữ nguyên. Chỉ là bằng chứng; mọi thay đổi do người dùng quyết định."""
    from . import docs
    return docs.term_report(store)


@tool
def search_knowledge(query: str, limit: int = 6) -> list[dict]:
    """Tìm trong kho kiến thức nhiếp ảnh/giáo án của trainer; trả về đoạn liên quan nhất kèm note."""
    from . import knowledge
    return knowledge.search(query, limit)


@tool
def get_knowledge(note: str = "") -> dict:
    """Lấy kho kiến thức. Trống = tree(); nếu không rỗng = get(note)."""
    from . import knowledge
    if not note:
        return knowledge.tree()
    return knowledge.get(note)


@tool
def add_knowledge(note: str, text: str, section: str = "Câu hỏi học viên hay hỏi") -> dict:
    """Thêm nội dung vào một note trong kho kiến thức."""
    from . import knowledge
    return knowledge.add(note, text, section)


PUBLIC = False  # set by make_public(): callers' file paths are never read or written


def _md_source(source: str) -> tuple[str, Path | None]:
    """Markdown text, or a path to a .md file (relative paths resolve against the Obsidian vault folder)."""
    if not PUBLIC and "\n" not in source and len(source) < 500:
        for cand in (Path(source).expanduser(), *([obsidian.vault_dir() / source] if obsidian._cfg().get("vault") else [])):
            if cand.is_file():
                return cand.read_text(encoding="utf-8"), cand
    return source, None


@tool
def colorlab_article(source: str, kind: str = "", topic: str = "", level: str = "", archetype: str = "") -> dict:
    """Bài blog Markdown (text hoặc đường dẫn .md) → `Article` của Alpha ColorLab (10 loại khối) + problems.
    problems dùng đúng mã của cổng kiểm site (`validateForPublish`, `packProblems`) + `unverified` ([cần xác minh]).
    kind: article|knowledge · topic: setup|color|af|exposure|composition|lens|body|video|audio|post|gear|firmware
    · level: newbie|mid|pro · archetype: setup-guide|versus|technique|explainer|fix|gear|recipe (ghi đè frontmatter)."""
    from .blog import colorlab
    text, _ = _md_source(source)
    return colorlab.md_to_article(text, kind=kind, topic=topic, level=level, archetype=archetype)


@tool
def colorlab_html(source: str, out: str = "", fragment: bool = False) -> dict:
    """Bài blog → HTML giống trang /blog của Alpha ColorLab (nền giấy, Noto Sans nhúng sẵn, JSON-LD).
    fragment=True: chỉ khối <article class="clab"> + CSS phạm vi .clab để dán vào CMS.
    out: đường dẫn file; trống thì ghi cạnh file .md (<slug>.html) hoặc trả HTML nếu nguồn là text."""
    from .blog import colorlab
    from .blog.colorlab_html import render_article
    text, path = _md_source(source)
    r = colorlab.md_to_article(text)
    html = render_article(r["article"], standalone=not fragment)
    target = None if PUBLIC else Path(out).expanduser() if out else (path.with_name(r["article"]["id"] + (".fragment" if fragment else "") + ".html") if path else None)
    if target is None:
        return {"html": html, "problems": r["problems"], "notes": r["notes"]}
    target.write_text(html, encoding="utf-8")
    return {"path": str(target), "bytes": len(html.encode()), "problems": r["problems"], "notes": r["notes"]}


@tool
def colorlab_pack(sources: list[str], name: str, repo: str = "", overwrite: bool = False) -> dict:
    """Ghi các bài (Markdown/đường dẫn) thành content pack `src/lib/lab/packs/<name>.ts` trong repo site, đăng ký
    vào PACKS rồi chạy cổng kiểm của site (`npx vitest run src/lib/lab/packs`). Từ chối nếu bài còn problems;
    cổng trượt thì hoàn tác. Không bao giờ chạy push:lab — trả lệnh để chủ site tự chạy (bài vào dạng nháp).
    repo trống: dùng "colorlab_repo" trong config.json."""
    from .blog import colorlab
    repo = repo or obsidian._cfg().get("colorlab_repo", "")
    if not repo:
        return {"ok": False, "problems": [f'thêm "colorlab_repo" vào {paths.CONFIG} hoặc truyền repo']}
    results = [colorlab.md_to_article(_md_source(s)[0]) for s in sources]
    blocked = {r["article"]["id"]: r["problems"] for r in results if r["problems"]}
    if blocked:
        return {"ok": False, "problems": blocked, "hint": "sửa bài rồi chạy lại; colorlab_article để xem chi tiết"}
    packs = Path(repo).expanduser() / "src/lib/lab/packs"
    index_before = (packs / "index.ts").read_text(encoding="utf-8") if (packs / "index.ts").exists() else None
    existed = (packs / f"{name}.ts").exists()
    out = colorlab.write_pack(results, repo, name, overwrite=overwrite)
    if out.get("gate") == "failed":
        if index_before is not None:
            (packs / "index.ts").write_text(index_before, encoding="utf-8")
        if not existed:
            (packs / f"{name}.ts").unlink(missing_ok=True)
        out["rolled_back"] = True
    return out


WRITE_TOOLS = ("record_term", "record_feedback", "remember_translation", "ban_term", "keep_english", "learn",
               "disable_rule", "commit_memory", "xls_read", "xls_write", "xls_review", "obsidian_export", "obsidian_import", "obsidian_audit_note", "ingest_docs", "add_knowledge", "colorlab_pack")


def make_public() -> None:
    """Mode for a server open to the Internet: drop write tools, never touch callers' file paths,
    never fetch URLs taken from callers' text (citation_checker then reports tiers only)."""
    import os
    global PUBLIC
    PUBLIC = True
    os.environ["SONY_VN_NO_NET"] = "1"
    for name in WRITE_TOOLS:
        mcp._tool_manager._tools.pop(name, None)


def main():
    """stdio (Claude Code, Gemini CLI) by default; --http for remote clients (ChatGPT developer mode, other MCP hosts)."""
    import argparse
    import sys
    ap = argparse.ArgumentParser(prog="sony-alpha-viet-mcp")
    ap.add_argument("--http", action="store_true", help="chạy HTTP thay vì stdio: MCP ở /mcp, REST JSON ở /v1/<tool>")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--read-only", action="store_true", help="tắt các tool ghi dữ liệu và đọc/ghi file (nên bật khi mở ra Internet)")
    a = ap.parse_args()
    if a.read_only:
        make_public()
    elif a.host not in ("127.0.0.1", "localhost", "::1"):
        print("Cảnh báo: write tools bị vô hiệu hóa trên non-loopback host", file=sys.stderr)
        make_public()
    if a.http:
        import uvicorn
        from .api import build_app
        uvicorn.run(build_app(), host=a.host, port=a.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
