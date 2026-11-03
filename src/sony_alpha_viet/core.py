"""Rules engine, audit, OSD width estimate and translation-memory search for Sony Vietnamese OSD menus."""
from __future__ import annotations

import difflib
import json
import os
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from .paths import DATA

TOKEN_RE = re.compile(r"<c[0-9A-Fa-f]+>|\$\{[^}]*\}")
ICON_PREFIX_RE = re.compile(r"^((?:<c[0-9A-Fa-f]+>\s*)*)(.*)$", re.S)
VI_CHARS = re.compile(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", re.I)
NON_LATIN = re.compile(r"[^\x00-\u024f\u1e00-\u1eff]")
FOREIGN = re.compile(r"[çñüöäëïßåøæœÇÑÜÖÄ]")
TONES = re.compile(r"[àáạảãầấậẩẫằắặẳẵèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ]")
# Vietnamese syllables written without diacritics; not treated as English residue.
VI_ASCII = set("""a an anh ba bao bi binh bo cho cao chi chu con cu da dai dan di du em gan ghi gia giao gio hai hay hoa hoi hon im in kem khi kho
khoa khong la lai lam lan len loa loai lo ma mai man mau mo mot nay nam neu ngay nhanh nhat nho noi on phim qua quay sang sao sau so ta tai tam tan
tay thao theo thi thoi thu ti tim tin to toi trai trong tu va vao ve vi voi xem xa xin xoay ho hop cam nhan bang tren duoi xanh nhau nhi ra tranh chia
tia tinh minh chinh danh sinh kinh hinh linh canh ganh banh mach sach thanh tuy hoan nguy khu kia tri ty ky ly my hy quy thuy lui tui mui mua chua mi
gi hi ni li ki tiu chiu thay khung gian mong truy tra pin quan trung cong do dung phong ban duy khe vui tua xe ngang trang gam bay quanh xung nghe
chim huy sai neon chung che pha rung tele khai xu cung sung tham mang chip web de""".split())


def nfc(s: str | None) -> str:
    return unicodedata.normalize("NFC", s or "")


def _load(name, default):
    p = DATA / name
    if not p.exists():
        return default
    if name.endswith(".jsonl"):
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(p.read_text(encoding="utf-8"))


def _save(name, obj):
    p = DATA / name
    tmp = p.with_suffix(p.suffix + ".tmp")
    if name.endswith(".jsonl"):
        tmp.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in obj), encoding="utf-8")
    else:
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _append(name, obj):
    with open(DATA / name, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


DATA_FILES = ("glossary.json", "rules.json", "exceptions.json", "tm.jsonl", "feedback.jsonl", "keep_english.json")


def _stamp() -> tuple:
    out = []
    for n in DATA_FILES:
        try:
            st = (DATA / n).stat()
            out.append((n, st.st_mtime_ns, st.st_size))
        except FileNotFoundError:
            out.append((n, 0, 0))
    return tuple(out)


class Store:
    """All persistent knowledge: glossary, rules, exceptions, translation memory, feedback."""

    def __init__(self):
        self.reload()

    def refresh(self) -> bool:
        """Reload if another process (second MCP server, Gemini CLI, a script) changed the data files since we read them."""
        if _stamp() != self._stamp:
            self.reload()
            return True
        return False

    def mark_current(self):
        """Our own writes are the new baseline."""
        self._stamp = _stamp()

    def reload(self):
        self.glossary = _load("glossary.json", [])
        self.rules = _load("rules.json", {"substitutions": [], "exact": {}, "banned": []})
        self.exceptions = _load("exceptions.json", {})
        self.tm = _load("tm.jsonl", [])
        self.feedback = _load("feedback.jsonl", [])
        self.keep = _load("keep_english.json", [])
        self.allow = set()
        for k, v in self.exceptions.items():
            if isinstance(v, list):
                for term in v:
                    self.allow.update(term.split())
        self._index()
        self._stamp = _stamp()

    def _index(self):
        self.gl_by_en = {g["en"].lower(): g for g in self.glossary}
        self.tm_by_en = defaultdict(list)
        self.tm_words = defaultdict(set)
        for i, t in enumerate(self.tm):
            self.tm_by_en[_key(t["en"])].append(i)
            for w in set(re.findall(r"[a-z]{3,}", t["en"].lower())):
                self.tm_words[w].add(i)
        # Add keep_english terms to allow list to prevent english_residue errors
        for entry in getattr(self, 'keep', []):
            term = entry.get("term", "")
            if term:
                joined = term.replace(" ", "")  # "Time Code" is also written "timecode"/"Timecode"
                for form in {term, joined, joined.capitalize()}:
                    self.allow.add(form)
                    self.allow.add(form.lower())
                    self.allow.update(form.split())
        # loanwords/kept terms are valid in any case ("Flash tự động" at the start of a label); other exceptions stay case-exact
        self.allow_lower = {w.lower() for x in self.exceptions.get("loanwords", []) for w in x.split()}
        self.allow_lower |= {w.lower() for k in getattr(self, "keep", []) for w in (k.get("term", ""), k.get("term", "").replace(" ", ""))}
        self._compiled = []
        for s in self.rules.get("substitutions", []):
            if s.get("disabled"):
                continue
            try:
                self._compiled.append((s, re.compile(s["pattern"])))
            except re.error:
                pass

    # ---------- persistence helpers ----------
    def save_glossary(self):
        self.glossary.sort(key=lambda g: g["en"].lower())
        _save("glossary.json", self.glossary)

    def save_rules(self):
        _save("rules.json", self.rules)

    def save_tm(self):
        _save("tm.jsonl", self.tm)

    def save_keep_english(self):
        _save("keep_english.json", self.keep)


def _key(en: str) -> str:
    return re.sub(r"\s+", " ", TOKEN_RE.sub("", en)).strip().lower()


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


# ---------------- OSD width estimate ----------------
_FONT_CANDIDATES = [
    os.environ.get("SONY_VN_FONT", ""),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_font_cache: dict = {}


def _font(h: int):
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    if h not in _font_cache:
        _font_cache[h] = None
        for p in _FONT_CANDIDATES:
            if p and os.path.exists(p):
                _font_cache[h] = ImageFont.truetype(p, h)
                break
    return _font_cache[h]


def est_width(text: str, font_w: float, font_h: float) -> float:
    """Substitute-font estimate calibrated on Sony UniversOTS strings (0.92 of Max Width = safe)."""
    text = re.sub(r"<c[0-9A-Fa-f]{4}>", "W", text)
    text = re.sub(r"\$\{v\d+(:\d+)?\}", "00", text)
    f = _font(int(round(float(font_h))))
    if f is None:
        return len(text) * 0.5 * float(font_w)
    return f.getlength(text) * (float(font_w) / float(font_h))


def effective_layout(en: str, layout: dict | None) -> dict | None:
    """With Line Feed Off the source's own line breaks are allowed: Sony's approved data has 2-line strings declared rows=1
    (e.g. "…memory card.\\nSlot 1"). Allowed lines = max(declared rows, source lines)."""
    if not layout or str(layout.get("linefeed", "Off")).lower() == "on" or not en:
        return layout
    n = en.replace("\\n", "\n").count("\n") + 1
    return {**layout, "rows": max(int(layout.get("rows") or 1), n)}


def fit(text: str, max_w, font_w=27, font_h=36, rows=1, linefeed="Off") -> dict:
    """Return verdict OK / BORDER (93-100%) / OVER, lines needed and worst line ratio."""
    mw = float(max_w)
    lines = text.replace("\\n", "\n").split("\n")
    if str(linefeed).lower() != "on":
        n = len(lines)
        worst = max(est_width(l, font_w, font_h) for l in lines) / mw
    else:
        n, worst = 0, 0.0
        for l in lines:
            cur = ""
            for w in l.split(" "):
                trial = f"{cur} {w}".strip() if cur else w
                if est_width(trial, font_w, font_h) <= mw * 0.97 or not cur:
                    cur = trial
                else:
                    n += 1
                    worst = max(worst, est_width(cur, font_w, font_h) / mw)
                    cur = w
            n += 1
            worst = max(worst, est_width(cur, font_w, font_h) / mw)
    r = int(rows)
    verdict = "OVER" if (n > r or worst > 1.0) else ("BORDER" if worst > 0.92 and str(linefeed).lower() != "on" else "OK")
    return {"verdict": verdict, "lines": n, "max_lines": r, "ratio": round(worst, 2)}


# ---------------- keep_english helper ----------------
def _apply_keep_english(vi: str, en: str, keep_entries: list) -> str:
    """Apply keep_english conversions: replace variants in vi with the term using surface form from en."""
    for entry in keep_entries:
        en_pattern = entry.get("en_pattern")
        if not en_pattern:
            continue
        try:
            en_matches = list(re.finditer(en_pattern, en, re.IGNORECASE))
        except re.error:
            continue
        if not en_matches:
            continue
        vi_variants = entry.get("vi_variants", {})
        if not vi_variants:
            continue
        # Sort variants by length descending to replace longest first
        sorted_variants = sorted(vi_variants.items(), key=lambda x: -len(x[0]))
        for variant_vi, template in sorted_variants:
            # Process in reverse order to avoid position shifts; variant match is case-insensitive
            matches = list(re.finditer(re.escape(variant_vi), vi, re.IGNORECASE))
            for match_idx in range(len(matches) - 1, -1, -1):
                m = matches[match_idx]
                # Align match_idx-th VI match with match_idx-th EN match, fall back to last EN match
                surface = en_matches[min(match_idx, len(en_matches) - 1)].group(0)
                replacement = template.replace("{term}", surface)
                pre = vi[:m.start()]
                # Avoid doubled words, e.g. "mã" + template "mã {term}"
                head = replacement.split(" ")[0]
                if " " in replacement and pre.rstrip().lower().endswith(head.lower()):
                    replacement = replacement[len(head) + 1:]
                at_start = re.fullmatch(r"(?:<c[0-9A-Fa-f]+>\s*)*[\"“']?", pre) is not None or re.search(r"([.?!:]\s*\n?|[\"“'(])$", pre)
                if (at_start or m.group(0)[:1].isupper()) and replacement[:1].islower():
                    replacement = _cap(replacement)
                vi = vi[:m.start()] + replacement + vi[m.end():]
    return vi


# ---------------- rules engine ----------------
def apply_rules(store: Store, vi: str, en: str = "", layout: dict | None = None) -> dict:
    """Apply exact-string rules and regex substitutions (with width-driven fallback)."""
    vi = nfc(vi)
    m = ICON_PREFIX_RE.match(en or "")
    core_en = m.group(2).strip() if m else ""
    pre_vi = ICON_PREFIX_RE.match(vi).group(1)
    applied = []
    exact = store.rules.get("exact", {})
    approved = {store.tm[i]["vi"] for i in store.tm_by_en.get(_key(en), []) if store.tm[i].get("status", "").startswith(("approved", "user"))}
    if vi in approved:  # an approved (possibly width-shortened) form is never rewritten
        return _finish(vi, vi, [], layout, en)
    if core_en in exact and exact[core_en] and not (layout and fit(pre_vi + exact[core_en], **effective_layout(en, layout))["verdict"] == "OVER"):
        new = pre_vi + exact[core_en]
        if new != vi:
            applied.append({"rule": "exact", "en": core_en})
        return _finish(vi, new, applied, layout, en)

    def run(level):
        v = vi
        used = []
        for s, rx in store._compiled:
            if s.get("en_requires") and not re.search(s["en_requires"], en or ""):
                continue
            rep = s["replace"] if level == 0 or not s.get("fallback") else s["fallback"]

            def f(mm, rep=rep):
                out = mm.expand(rep)
                pre = mm.string[: mm.start()]
                at_start = re.fullmatch(r"(?:<c[0-9A-Fa-f]+>\s*)*[\"“]?", pre) is not None or re.search(r"([.?!:]\s*\n?|[\"“(])$", pre)
                if at_start and mm.group(0)[:1].isupper() and not out[:1].isupper():
                    out = _cap(out)
                return out

            nv = rx.sub(f, v)
            if nv != v:
                used.append(s["id"])
                v = nv
        mo = ICON_PREFIX_RE.match(vi)
        mn = re.match(r"^((?:<c[0-9A-Fa-f]+>\s*)*)(.)(.*)$", v, re.S)
        if mo and mo.group(2)[:1].isupper() and mn and mn.group(2).islower():
            v = mn.group(1) + mn.group(2).upper() + mn.group(3)
        return v, used

    new, used = run(0)
    if layout and fit(new, **effective_layout(en, layout))["verdict"] == "OVER":
        alt, used2 = run(1)
        if fit(alt, **effective_layout(en, layout))["verdict"] != "OVER" or len(alt) < len(new):
            new, used = alt, used2
    applied += [{"rule": u} for u in used]
    for s, _ in store._compiled:
        if s["id"] in used:
            s["hits"] = s.get("hits", 0) + 1
    # Apply keep_english conversions
    new = _apply_keep_english(new, en, store.keep)
    return _finish(vi, new, applied, layout, en)


def _finish(old, new, applied, layout, en=""):
    out = {"text": new, "changed": new != old, "applied": applied}
    if layout:
        out["fit"] = fit(new, **effective_layout(en, layout))
    return out


# ---------------- audit ----------------
def audit(store: Store, en: str, vi: str, layout: dict | None = None) -> dict:
    """List rule violations in a Vietnamese string."""
    issues = []
    if vi and nfc(vi) != vi:  # combining diacritics (NFD) look identical but may render wrong in the camera font
        issues.append({"type": "not_nfc", "fix": nfc(vi), "why": "dấu tổ hợp (NFD), cần ký tự dựng sẵn (NFC)"})
    vi = nfc(vi)
    en = en or ""
    # Check for keep_english variants that should not be flagged as english_residue
    kept_variants = set()
    for entry in store.keep:
        en_pattern = entry.get("en_pattern")
        if not en_pattern:
            continue
        try:
            if re.search(en_pattern, en, re.IGNORECASE):
                vi_variants = entry.get("vi_variants", {})
                for variant in vi_variants.keys():
                    if variant in vi:
                        kept_variants.add(variant)
                        # Flag the issue as keep_english instead of english_residue
                        expected = entry.get("vi_variants", {}).get(variant, "{term}").replace("{term}", entry.get("term", ""))
                        issues.append({"type": "keep_english", "found": variant, "expected": expected, "why": entry.get("why", "")})
        except re.error:
            continue

    enw = {w.lower() for w in re.findall(r"[^\W\d_][\w'\-]*", TOKEN_RE.sub(" ", en))}
    for w in re.findall(r"[\w'\-]+", TOKEN_RE.sub(" ", vi)):
        w = w.strip("'-")
        if re.search(r"\d", w) or NON_LATIN.search(w):
            continue
        if VI_CHARS.search(w) or w.lower() in VI_ASCII or w in store.allow or w.lower() in store.allow_lower or w.isupper() or len(w) < 2:
            continue
        if w.lower() in enw or re.search(r"[fjwz]", w.lower()):
            hint = _gl_hint(store, w)
            if not hint and w[:1].isupper() and w in en:
                issues.append({"type": "kept_english", "severity": "info", "word": w, "hint": "tên riêng/tên thành phố? nếu không phải, hãy dịch"})
            else:
                issues.append({"type": "english_residue", "word": w, "hint": hint})
    for b in store.rules.get("banned", []):
        mm = re.search(b["pattern"], vi)
        if mm:
            issues.append({"type": "banned", "match": mm.group(0), "why": b["why"]})
    for w in re.findall(r"\w+", TOKEN_RE.sub(" ", vi)):
        if not VI_CHARS.search(w) or FOREIGN.search(w) or w in store.allow:
            continue
        if len(TONES.findall(w.lower())) > 1:
            issues.append({"type": "glued_words", "word": w})
        elif re.search(r"(?<!n)g$|[^cn]h$|[bdđklqrsvx]$", w.lower()):
            issues.append({"type": "letter_dropping", "word": w})
    for mm in re.finditer(r"(?<![\d.\w])[^\W\d_]{1,2}\.[^\W\d_]{2,}", vi):
        if not re.match(r"v\.v", mm.group(0)):
            issues.append({"type": "abbreviation", "severity": "warn", "match": mm.group(0), "why": "không viết tắt; chỉ dùng khi không còn cách nào vừa khung"})
    te = sorted(TOKEN_RE.findall(en))
    tv = sorted(TOKEN_RE.findall(vi))
    if en and te != tv:
        issues.append({"type": "token_mismatch", "en_tokens": te, "vi_tokens": tv})
    if en and en.count("\n") != vi.count("\n") and layout and str(layout.get("linefeed", "Off")).lower() != "on":
        allowed = effective_layout(en, layout)["rows"]
        # approved Sony data reflows lines freely within the allowed rows; only more lines than allowed is an error
        issues.append({"type": "line_count", "en_lines": en.count("\n") + 1, "vi_lines": vi.count("\n") + 1, "allowed": allowed,
                       **({} if vi.count("\n") + 1 > allowed else {"severity": "info"})})
    if re.search(r"\d,\d", vi) and re.search(r"\d\.\d", en):
        issues.append({"type": "decimal_comma", "why": "dùng dấu chấm thập phân như tiếng Anh (0.3EV, f/2.8)"})
    k = _key(en)
    exact = store.rules.get("exact", {})
    core_en = ICON_PREFIX_RE.match(en).group(2).strip() if en else ""
    approved = [store.tm[i]["vi"] for i in store.tm_by_en.get(k, []) if store.tm[i].get("status", "").startswith(("approved", "user"))]
    if core_en in exact and ICON_PREFIX_RE.match(vi).group(2).strip() != exact[core_en] and vi not in approved:
        issues.append({"type": "exact_rule", "expected": exact[core_en]})
    if approved and vi not in approved:
        issues.append({"type": "inconsistent_with_memory", "approved_variants": sorted(set(approved))[:5]})
    out = {"ok": not any(i.get("severity", "error") == "error" for i in issues), "issues": issues}
    if layout:
        lay = effective_layout(en, layout)
        out["fit"] = fit(vi, **lay)
        if out["fit"]["verdict"] != "OK" and en:
            en_fit = fit(en, **lay)
            if en_fit["verdict"] == "OVER" and out["fit"]["ratio"] <= en_fit["ratio"] * 1.1:
                # the English source itself "overflows" by our estimate → the layout data or estimate is off, not the translation
                out["fit"]["verdict"] = "CHECK"
                issues.append({"type": "layout_suspect", "severity": "info", "en_ratio": en_fit["ratio"],
                               "why": "chính chuỗi tiếng Anh cũng vượt khung theo ước lượng; kiểm bằng SonyTool"})
        if out["fit"]["verdict"] not in ("OK", "CHECK"):
            out["ok"] = False
    return out


def _gl_hint(store, w):
    g = store.gl_by_en.get(w.lower())
    return f"{g['en']} = {g['vi']}" if g else None


# ---------------- lookup ----------------
def lookup_terms(store: Store, text: str, limit: int = 30) -> list[dict]:
    """Glossary entries whose English term occurs in text (longest first) or fuzzy-match a single query."""
    t = text.lower()
    hits = [g for g in store.glossary if len(g["en"]) > 1 and re.search(r"(?<![a-z])" + re.escape(g["en"].lower()) + r"(?![a-z])", t)]
    if not hits:
        names = difflib.get_close_matches(t, list(store.gl_by_en), n=limit, cutoff=0.6)
        hits = [store.gl_by_en[n] for n in names]
    hits.sort(key=lambda g: (not g.get("locked"), -len(g["en"])))
    return hits[:limit]


IMPLIED = ["chọn", "cài đặt", "thiết lập"]  # leading verbs the menu context already implies
IMPLIED_AFTER = ["chụp"]  # droppable only right after an IMPLIED verb ("Chọn chụp …"); alone it carries meaning


def suggest_short(store: Store, en: str, vi: str, layout: dict | None = None, limit: int = 5) -> list[dict]:
    """Shorter forms for a BORDER/OVER string that keep its meaning:
    (a) learned width-only rules, (b) approved translations of the SAME source string made for other layouts,
    (c) dropping implied words at the start/end only, (d) glossary short forms substituted in place.
    Never proposes another string's translation (that changed meaning, e.g. "update failed" → "updated")."""
    layout = effective_layout(en, layout)
    if not layout or fit(vi, **layout)["verdict"] == "OK":
        return []
    pre, core_vi = ICON_PREFIX_RE.match(vi).groups()
    tokens = sorted(TOKEN_RE.findall(vi))
    found, seen = [], {vi}

    def add(text, source):
        text = re.sub(r"\s+", " ", text).strip() if "\n" not in text else text.strip()
        if text and text not in seen and sorted(TOKEN_RE.findall(text)) == tokens:
            seen.add(text)
            found.append({"text": text, "fit": fit(text, **layout), "source": source})

    for s, rx in store._compiled:  # (a)
        if s.get("fallback") and rx.search(vi):
            add(rx.sub(s["fallback"], vi), f"fallback {s['id']}")
    for i in store.tm_by_en.get(_key(en), []):  # (b)
        e = store.tm[i]
        if e.get("status", "").startswith(("approved", "user")):
            add(pre + ICON_PREFIX_RE.match(e["vi"]).group(2), f"memory {e.get('id')} (cùng chuỗi gốc, khung {e.get('maxW', '?')}px)")
    words = core_vi.split(" ")  # (c) labels only: leading implied verbs ("Chọn chụp chống nhấp nháy" → "Chống nhấp nháy")
    is_label = len(words) <= 6 and not re.search(r"[.?!:,]\s|\n|[.?!]$", core_vi)
    n = 0
    while is_label and n < len(words):
        two = " ".join(words[n:n + 2]).lower()
        step = 2 if two in IMPLIED else 1 if words[n].lower() in IMPLIED or (n and words[n].lower() in IMPLIED_AFTER) else 0
        if not step:
            break
        n += step
        if len(words) - n >= 2:
            add(pre + _cap(" ".join(words[n:])), f"bỏ '{' '.join(words[:n])}' ở đầu")
    low_en = en.lower()  # (d)
    for g in store.glossary:
        sh = g.get("short")
        if sh and sh != g["vi"] and re.search(r"(?<![a-z])" + re.escape(g["en"].lower()) + r"(?![a-z])", low_en):
            m = re.search(r"(?<!\w)" + re.escape(g["vi"]) + r"(?!\w)", vi, re.IGNORECASE)
            if m:
                rep = _cap(sh) if m.group(0)[:1].isupper() else sh
                add(vi[:m.start()] + rep + vi[m.end():], f"dạng ngắn '{g['en']}'")
    rank = {"OK": 0, "BORDER": 1, "OVER": 2}
    found.sort(key=lambda c: (rank.get(c["fit"]["verdict"], 3), c["fit"]["ratio"]))
    return found[:limit]


def search_tm(store: Store, text: str, limit: int = 5, min_score: float = 0.55) -> list[dict]:
    k = _key(text)
    cand = set(store.tm_by_en.get(k, []))
    words = set(re.findall(r"[a-z]{3,}", text.lower()))
    scored = defaultdict(int)
    for w in words:
        idx = store.tm_words.get(w, ())
        if len(idx) > 1500:
            continue
        for i in idx:
            scored[i] += 1
    cand |= {i for i, _ in sorted(scored.items(), key=lambda x: -x[1])[:300]}
    res = []
    for i in cand:
        e = store.tm[i]
        s = difflib.SequenceMatcher(None, k, _key(e["en"])).ratio()
        if s >= min_score:
            res.append((s, e))
    res.sort(key=lambda x: (-x[0], x[1].get("status") != "user-approved"))
    out, seen = [], set()
    for s, e in res:
        sig = (e["en"], e["vi"])
        if sig in seen:
            continue
        seen.add(sig)
        out.append({"score": round(s, 3), "en": e["en"], "vi": e["vi"], "id": e.get("id"), "project": e.get("project"),
                    "status": e.get("status"), "layout": {k2: e.get(k2) for k2 in ("maxW", "fontW", "fontH", "rows", "linefeed")}})
        if len(out) >= limit:
            break
    return out
