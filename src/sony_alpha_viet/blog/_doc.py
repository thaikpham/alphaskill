"""Parser dùng chung cho các tool blog (aio, seo, brand, freshness, citation, blog_audit).

Đọc bài một lần, mọi tool dùng chung số dòng và vùng văn xuôi:
- Article.lines: cùng số dòng với bài gốc (dòng n = lines[n-1]). Frontmatter, comment HTML,
  <script>, code fence bị thay bằng dòng trống nên không bị đếm như văn xuôi.
- Article.raw_lines: bài đã chuẩn hóa (NFC, bỏ BOM, CRLF -> LF), dùng để đọc JSON-LD.
- Biểu thức (regex) so với văn bản đã bỏ dấu: viết chữ thường, không dấu (xem fold()).
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import unicodedata
from urllib.parse import urlparse

HEADING_RX = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
BULLET_RX = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(\S.*)$")
TASK_RX = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s+(\S.*)$")
SEP_RX = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*$")
TLDR_RX = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*|__)?\s*(TL;DR|Tóm tắt|Tóm lại)(?=\s*(?::|\*\*|__|$))"
    r"\s*(?:\*\*|__)?\s*:?\s*(?:\*\*|__)?\s*(.*)$",
    re.IGNORECASE,
)
QUESTION_BOLD_RX = re.compile(r"^\s*(?:\*\*|__)([^*_\n]+?\?)(?:\*\*|__)\s*(.*)$")
SOURCE_WORD_RX = re.compile(r"nguon|source|theo (?:sony|dpreview|cong bo)|cong bo chinh thuc|sony official|sony\.com|https?://")
STRUCT_RX = re.compile(r"^(?:#|\||[-*+]\s|\d+[.)]\s|>|<)")


def normalize(md: str) -> str:
    """NFC, bỏ BOM, đổi CRLF/CR thành LF."""
    return unicodedata.normalize("NFC", md or "").lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def fold(s: str) -> str:
    """Chữ thường, bỏ dấu tiếng Việt, đ -> d. Dùng để so khớp không phân biệt dấu."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def words_of(s: str) -> int:
    """Số từ: token có ít nhất một chữ/số (bỏ dấu gạch, dấu |, ký hiệu đứng riêng)."""
    return sum(1 for t in s.split() if re.search(r"\w", t))


def quote(s: str, n: int = 100) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def band(score: float) -> str:
    """Thang điểm duy nhất: ≥80 Đạt, 60–79 Cần sửa, <60 Thấp."""
    return "Đạt" if score >= 80 else "Cần sửa" if score >= 60 else "Thấp"


def as_date(v) -> _dt.date:
    """Ngày tham chiếu: date, 'YYYY-MM-DD', 'DD/MM/YYYY', 'MM/YYYY' hoặc '' (hôm nay)."""
    if isinstance(v, _dt.date):
        return v
    s = (v or "").strip()
    if not s:
        return _dt.date.today()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%Y"):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Ngày không hợp lệ: {v} (dùng YYYY-MM-DD)")


def parse_frontmatter(raw_lines: list[str]) -> tuple[dict, int]:
    """(frontmatter, số dòng bị frontmatter chiếm). YAML thật; nếu lỗi thì parse lỏng."""
    if not raw_lines or raw_lines[0].strip() != "---":
        return {}, 0
    end = next((i for i in range(1, len(raw_lines)) if raw_lines[i].strip() == "---"), None)
    if end is None:
        return {}, 0
    try:
        import yaml

        data = yaml.safe_load("\n".join(raw_lines[1:end]))
        if isinstance(data, dict):
            # ngày và số giữ dạng chữ, ví dụ updated: 02/11/2026 vẫn là "02/11/2026"
            fm = {str(k): (v if isinstance(v, (list, bool)) else "" if v is None else str(v)) for k, v in data.items()}
            return fm, end + 1
    except Exception:
        pass
    fm = {}
    for line in raw_lines[1:end]:
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            v = re.sub(r"\s+#.*$", "", v.strip())
            if v.startswith("["):
                fm[k.strip()] = [x.strip().strip("\"'") for x in v.strip("[]").split(",") if x.strip()]
            else:
                fm[k.strip()] = v.strip("\"'")
    return fm, end + 1


def _mask(raw_lines: list[str], fm_end: int) -> list[str]:
    """Thay vùng không phải văn xuôi bằng dòng trống, giữ nguyên số dòng."""
    out = list(raw_lines)
    for i in range(min(fm_end, len(out))):
        out[i] = ""
    text = "\n".join(out)
    text = re.sub(
        r"<!--.*?-->|<script\b[^>]*>.*?</script>",
        lambda m: "\n" * m.group(0).count("\n"),
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    out = text.split("\n")
    fence = None
    for i, ln in enumerate(out):
        m = re.match(r"^\s*(`{3,}|~{3,})", ln)
        if fence is None:
            if m:
                fence = m.group(1)
                out[i] = ""
        else:
            out[i] = ""
            if m and ln.strip() == fence:
                fence = None
    return out


def jsonld(markdown: str) -> list[dict]:
    """Mọi node JSON-LD trong bài (kể cả trong code fence). Node lỗi có khóa _error."""
    out: list[dict] = []
    for block in re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", markdown, re.DOTALL | re.IGNORECASE):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            out.append({"_error": "JSON không hợp lệ"})
            continue
        if isinstance(data, dict):
            nodes = data.get("@graph", [data])
        elif isinstance(data, list):
            nodes = data
        else:
            nodes = []
        out.extend(n for n in (nodes if isinstance(nodes, list) else []) if isinstance(n, dict))
    return out


def count_words(markdown) -> int:
    """Số từ văn xuôi: bỏ frontmatter, code, JSON-LD, dòng bảng. Nhận markdown (str) hoặc Article."""
    a = as_article(markdown)
    return sum(words_of(ln) for ln in a.lines if not ln.lstrip().startswith("|"))


def tldr(a: "Article") -> dict:
    """TL;DR ngay dưới H1 (trước heading kế tiếp). Bullet hoặc đoạn đều đếm như nhau.

    Trả về {words, form, labelled, line, quote}. Không có nhãn thì lấy đoạn đầu sau H1 (labelled=False).
    """
    empty = {"words": 0, "form": "", "labelled": False, "line": 0, "quote": ""}
    if a.h1 is None:
        return empty
    start = a.h1[0]
    end = a.end_of(start, 6)
    body = a.lines[start:end]
    for k, ln in enumerate(body):
        m = TLDR_RX.match(ln)
        if not m:
            continue
        rest = m.group(2).strip()
        j = k + 1
        if not rest:
            while j < len(body) and not body[j].strip():
                j += 1
            if j < len(body) and BULLET_RX.match(body[j]):
                bullets = []
                while j < len(body) and BULLET_RX.match(body[j]):
                    bullets.append(BULLET_RX.match(body[j]).group(1))
                    j += 1
                return {"words": sum(words_of(b) for b in bullets), "form": f"{len(bullets)} bullet",
                        "labelled": True, "line": start + k + 1, "quote": quote(bullets[0])}
        para = [rest] if rest else []
        while j < len(body) and body[j].strip():
            para.append(body[j].strip())
            j += 1
        text = " ".join(para)
        return {"words": words_of(text), "form": "đoạn", "labelled": True, "line": start + k + 1, "quote": quote(text)}
    for k, ln in enumerate(body):
        if ln.strip() and not STRUCT_RX.match(ln.strip()):
            para, j = [], k
            while j < len(body) and body[j].strip() and not STRUCT_RX.match(body[j].strip()):
                para.append(body[j].strip())
                j += 1
            text = " ".join(para)
            return {"words": words_of(text), "form": "đoạn đầu", "labelled": False, "line": start + k + 1, "quote": quote(text)}
    return empty


def stamps(a: "Article") -> list[dict]:
    """Mốc cập nhật: 'Cập nhật 11/2026', 'Cập nhật 02/11/2026', 'Cập nhật 2026-11-02' và frontmatter updated."""
    out: list[dict] = []
    rx = re.compile(r"cap nhat\b[^\n]{0,40}?(?:(\d{1,2})/(\d{1,2})/(\d{4})|(\d{4})-(\d{2})-(\d{2})|(\d{1,2})/(\d{4}))")
    for lineno, ln in a.grep(r"cap nhat"):
        for m in rx.finditer(fold(ln)):
            try:
                if m.group(3):
                    d = _dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                elif m.group(4):
                    d = _dt.date(int(m.group(4)), int(m.group(5)), int(m.group(6)))
                else:
                    d = _dt.date(int(m.group(8)), int(m.group(7)), 1)
            except ValueError:
                continue
            out.append({"date": d, "line": lineno, "quote": quote(ln)})
    up = a.fm.get("updated", "")
    if isinstance(up, str):
        for pat, order in ((r"(\d{1,2})/(\d{1,2})/(\d{4})", "dmy"), (r"(\d{4})-(\d{2})-(\d{2})", "ymd")):
            m = re.search(pat, up)
            if m:
                try:
                    g = [int(x) for x in m.groups()]
                    d = _dt.date(g[2], g[1], g[0]) if order == "dmy" else _dt.date(g[0], g[1], g[2])
                    out.append({"date": d, "line": 0, "quote": f"updated: {up}"})
                except ValueError:
                    pass
                break
    return out


class Article:
    """Bài đã phân tích. Mọi số dòng là 1-based."""

    def __init__(self, markdown: str):
        self.raw = normalize(markdown)
        self.raw_lines = self.raw.split("\n")
        self.fm, fm_end = parse_frontmatter(self.raw_lines)
        self.lines = _mask(self.raw_lines, fm_end)
        self.jsonld = jsonld(self.raw)
        self.headings: list[tuple[int, int, str]] = []  # (dòng, cấp, tiêu đề)
        for i, ln in enumerate(self.lines):
            m = HEADING_RX.match(ln)
            if m:
                self.headings.append((i + 1, len(m.group(1)), m.group(2).strip()))
        self.h1 = next((h for h in self.headings if h[1] == 1), None)

    @property
    def prose(self) -> str:
        return "\n".join(self.lines)

    def grep(self, pattern: str) -> list[tuple[int, str]]:
        """(dòng, nội dung gốc) có dòng khớp pattern. Pattern viết theo dạng fold()."""
        rx = re.compile(pattern)
        return [(i + 1, ln) for i, ln in enumerate(self.lines) if rx.search(fold(ln))]

    def end_of(self, lineno: int, level: int) -> int:
        """Chỉ số (0-based, exclusive) kết thúc phần thân của heading ở dòng lineno, trước heading cùng hoặc cao hơn."""
        for ln2, lv2, _ in self.headings:
            if ln2 > lineno and lv2 <= level:
                return ln2 - 1
        return len(self.lines)

    def section(self, title_rx: str, level: int = 2):
        """(dòng heading, chỉ số kết thúc) của mục có tiêu đề khớp title_rx (dạng fold). None nếu không có."""
        for ln, lv, title in self.headings:
            if lv == level and re.search(title_rx, fold(title)):
                return ln, self.end_of(ln, level)
        return None

    def h2_sections(self) -> list[tuple[int, str, int]]:
        return [(ln, title, self.end_of(ln, 2)) for ln, lv, title in self.headings if lv == 2]

    def faq(self) -> list[dict]:
        """[{q, a, line, words}] từ mục FAQ. Câu hỏi là '### ...?' hoặc '**...?**' ở đầu dòng."""
        sec = self.section(r"^(faq|cau hoi thuong gap|hoi dap)\b")
        if not sec:
            return []
        start, end = sec[0], sec[1]
        out: list[dict] = []
        cur = None
        for idx in range(start, end):
            ln = self.lines[idx]
            m3 = re.match(r"^###\s+(.+\?)\s*$", ln)
            qb = None if m3 else QUESTION_BOLD_RX.match(ln)
            if m3 or qb:
                if cur:
                    out.append(cur)
                q = (m3.group(1) if m3 else qb.group(1)).strip()
                rest = "" if m3 else qb.group(2).strip()
                cur = {"q": q, "parts": [rest] if rest else [], "line": idx + 1}
            elif HEADING_RX.match(ln):
                if cur:
                    out.append(cur)
                cur = None
            elif cur is not None and ln.strip():
                cur["parts"].append(ln.strip())
        if cur:
            out.append(cur)
        for f in out:
            f["a"] = " ".join(f.pop("parts"))
            f["words"] = words_of(f["a"])
        return out

    def tables(self) -> list[dict]:
        """[{line, cols, header, rows}] cho bảng Markdown đúng (có dòng phân cách)."""
        out = []
        for i in range(len(self.lines) - 1):
            if "|" in self.lines[i] and SEP_RX.match(self.lines[i + 1]):
                header = [c.strip() for c in self.lines[i].strip().strip("|").split("|")]
                rows = 0
                for ln in self.lines[i + 2:]:
                    if "|" in ln and ln.strip():
                        rows += 1
                    else:
                        break
                out.append({"line": i + 1, "cols": len(header), "header": header, "rows": rows})
        return out

    def task_items(self) -> list[tuple[int, str]]:
        return [(i + 1, m.group(1)) for i, ln in enumerate(self.lines) if (m := TASK_RX.match(ln))]

    def blocks(self) -> list[list[tuple[int, str]]]:
        """Khối dòng liên tiếp không trống, không phải heading (đoạn, bullet, bảng): [[(dòng, nội dung)]]."""
        out: list[list[tuple[int, str]]] = []
        cur: list[tuple[int, str]] = []
        for i, ln in enumerate(self.lines):
            if not ln.strip() or HEADING_RX.match(ln):
                if cur:
                    out.append(cur)
                    cur = []
                continue
            cur.append((i + 1, ln))
        if cur:
            out.append(cur)
        return out


def as_article(x) -> Article:
    """Nhận markdown (str) hoặc Article đã phân tích."""
    return x if isinstance(x, Article) else Article(x)


SITE_HOSTS = ("alphacolorlab.com",)
IMG_RX = re.compile(r"!\[[^\]\n]*\]\([^)\n]*\)")
MD_LINK_RX = re.compile(r"(?<!!)\[([^\]\n]*)\]\(\s*<?([^)\s>]*)[^)\n]*\)")
BARE_URL_RX = re.compile(r"https?://[^\s<>\"'\]\)]+")
PLACEHOLDER_RX = re.compile(r"\[link\s+n\w*\s+b\w*:[^\]\n]*\]", re.IGNORECASE)
URL_TRAIL = ".,;:!?…"


def _internal(url: str) -> bool:
    """Nội bộ: đường dẫn tương đối hoặc thuộc alphacolorlab.com."""
    p = urlparse(url)
    if not p.netloc:
        return True
    host = (p.hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in SITE_HOSTS)


def links(a) -> list[dict]:
    """Link trong bài (vùng không phải văn xuôi đã bị bỏ): [{line, url, text, kind, internal}].

    kind: md ([chữ](url)), bare (URL trần), placeholder ([link nội bộ: …], luôn tính là nội bộ).
    Bỏ ảnh, neo (#...), mailto/tel; bỏ dấu câu cuối; trùng URL (hoặc placeholder) chỉ tính một lần.
    """
    a = as_article(a)
    out: list[dict] = []
    seen: set = set()

    def add(line: int, url: str, text: str, kind: str) -> None:
        key = ("ph", fold(text)) if kind == "placeholder" else ("url", url)
        if key in seen:
            return
        seen.add(key)
        out.append({"line": line, "url": url, "text": text, "kind": kind,
                    "internal": kind == "placeholder" or _internal(url)})

    for i, raw in enumerate(a.lines, 1):
        s = IMG_RX.sub(lambda m: " " * len(m.group(0)), raw)
        for m in MD_LINK_RX.finditer(s):
            url = m.group(2).rstrip(URL_TRAIL)
            if url and not url.startswith("#") and urlparse(url).scheme in ("", "http", "https"):
                add(i, url, m.group(1).strip() or url, "md")
        s = MD_LINK_RX.sub(lambda m: " " * len(m.group(0)), s)
        for m in BARE_URL_RX.finditer(s):
            url = m.group(0).rstrip(URL_TRAIL)
            add(i, url, url, "bare")
        for m in PLACEHOLDER_RX.finditer(raw):
            add(i, "", m.group(0), "placeholder")
    return out


def finding(criterion: int, item: str, ok: bool, evidence: str, fix: str = "", hits=(), manual: bool = False) -> dict:
    """Kết quả một tiêu chí. hits là [(dòng, trích đoạn)] các chỗ lỗi; line/quote lấy từ hit đầu.
    manual=True: cần người duyệt, không phải fail (gọi với ok=False)."""
    rows = [{"line": ln, "quote": q} for ln, q in hits]
    first = rows[0] if rows else {"line": 0, "quote": ""}
    return {"criterion": criterion, "item": item, "pass": bool(ok), "manual": bool(manual), "evidence": evidence,
            "fix": "" if ok else fix, "line": first["line"], "quote": first["quote"], "hits": rows}
