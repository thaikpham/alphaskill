"""Long-term memory and self-improvement: decisions, corrections, rule learning."""
from __future__ import annotations

import datetime as _dt
import difflib
import re
import subprocess
from collections import Counter

from .core import DATA, Store, _append, _key, nfc

LOG = DATA / "LEARNING_LOG.md"


def _now():
    return _dt.datetime.now().isoformat(timespec="seconds")


def _log(line: str):
    if not LOG.exists():
        LOG.write_text("# Nhật ký tự học\n\n", encoding="utf-8")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"- {_now()} - {line}\n")


def record_term(store: Store, en: str, vi: str, short: str = "", note: str = "", locked: bool = True) -> dict:
    """User-approved glossary decision. Locked terms win over imported ones."""
    en, vi = en.strip(), nfc(vi.strip())
    g = store.gl_by_en.get(en.lower())
    old = dict(g) if g else None
    entry = {"en": en, "vi": vi, "short": nfc(short) or vi, "category": (g or {}).get("category", "user"),
             "note": note, "source": "user", "locked": locked, "updated": _now()}
    if g:
        g.clear(); g.update(entry)
    else:
        store.glossary.append(entry)
    store.save_glossary(); store._index()
    _log(f"Thuật ngữ: **{en}** = {vi}" + (f" (trước: {old['vi']})" if old and old['vi'] != vi else "") + (f" - {note}" if note else ""))
    return {"saved": entry, "previous": old}


def ban_term(store: Store, pattern: str, why: str) -> dict:
    re.compile(pattern)
    store.rules.setdefault("banned", []).append({"pattern": pattern, "why": why, "source": "user", "added": _now()})
    store.save_rules()
    _log(f"Cấm dùng `{pattern}` - {why}")
    return {"banned": pattern}


def remember_translation(store: Store, en: str, vi: str, project: str = "", layout: dict | None = None, status: str = "user-approved") -> dict:
    """Store an approved EN→VI pair in translation memory (replaces earlier entries of the same EN in the same project)."""
    en, vi = en, nfc(vi)
    k = _key(en)
    replaced = 0
    for i in store.tm_by_en.get(k, []):
        e = store.tm[i]
        if e.get("project") == project or not project:
            if e["vi"] != vi:
                e["vi"], e["status"], e["updated"] = vi, status, _now(); replaced += 1
    if not replaced and not any(store.tm[i]["vi"] == vi for i in store.tm_by_en.get(k, [])):
        rec = {"id": f"u{len(store.tm)}", "en": en, "vi": vi, "project": project, "status": status, "added": _now()}
        rec.update(layout or {})
        store.tm.append(rec)
    store.save_tm(); store._index()
    return {"stored": True, "replaced": replaced}


def keep_english(store: Store, term: str, vi_variants: dict, en_pattern: str = "", why: str = "", apply: bool = False) -> dict:
    """Manage keep_english term: terms that stay in English because Vietnamese doesn't help.
    vi_variants: maps Vietnamese variant → replacement template (use {term} for the term).
    Returns plan; when apply=True executes it and saves all files.
    """
    import re
    from .core import _apply_keep_english

    # Build en_pattern if not provided: case-insensitive word-boundary regex of term
    if not en_pattern:
        escaped = re.escape(term)
        en_pattern = r"(?i)\b" + escaped.replace(r"\ ", r"\s*") + r"\b"

    plan = {
        "term": term,
        "vi_variants": vi_variants,
        "en_pattern": en_pattern,
        "why": why,
        "rules_to_disable": [],
        "exact_changes": [],
        "glossary_changes": [],
        "tm_changes": {"count": 0, "changes": []},
    }

    entry = {"term": term, "en_pattern": en_pattern, "vi_variants": vi_variants}
    conv = lambda vi, en: _apply_keep_english(vi, en, [entry])

    def _plain(pattern):  # "[Zz]oom" -> "zoom" so the term is found inside regex patterns
        return re.sub(r"\[([A-Za-z])([A-Za-z])\]", lambda m: m.group(1) if m.group(1).lower() == m.group(2).lower() else m.group(0), pattern).lower().replace("\\", "")

    # Rules to disable: substitutions whose replace/fallback contains a variant and whose pattern mentions the term
    term_lower, term_nospace = term.lower(), term.lower().replace(" ", "")
    for s in store.rules.get("substitutions", []):
        pat = _plain(s.get("pattern", "")) + " " + (s.get("learned_from") or "").lower()
        out = (s.get("replace") or "").lower() + " " + (s.get("fallback") or "").lower()
        if (term_lower in pat or term_nospace in pat.replace(" ", "")) and any(v.lower() in out for v in vi_variants) and not s.get("disabled"):
            plan["rules_to_disable"].append({"id": s["id"], "pattern": s["pattern"], "replace": s.get("replace")})

    exact = store.rules.get("exact", {})
    for en_key, vi_val in exact.items():
        if re.search(en_pattern, en_key) and conv(vi_val, en_key) != vi_val:
            plan["exact_changes"].append({"en": en_key, "old": vi_val, "new": conv(vi_val, en_key)})

    for g in store.glossary:
        if re.search(en_pattern, g["en"]):
            nv, ns = conv(g["vi"], g["en"]), conv(g.get("short") or g["vi"], g["en"])
            if nv != g["vi"] or ns != (g.get("short") or g["vi"]):
                plan["glossary_changes"].append({"en": g["en"], "old": {"vi": g["vi"], "short": g.get("short")}, "new": {"vi": nv, "short": ns}})
    if not store.gl_by_en.get(term.lower()):
        plan["glossary_changes"].append({"en": term, "old": None, "new": {"vi": term, "short": term, "locked": True}})

    tm_changes = []
    for i, t in enumerate(store.tm):
        if re.search(en_pattern, t.get("en", "")):
            nv = conv(t["vi"], t["en"])
            if nv != t["vi"]:
                tm_changes.append({"idx": i, "id": t.get("id", f"u{i}"), "en": t["en"], "before": t["vi"], "after": nv})

    plan["tm_changes"]["count"] = len(tm_changes)
    plan["tm_changes"]["changes"] = [{k: v for k, v in c.items() if k != "idx"} for c in tm_changes[:30]]

    if not apply:
        return plan

    # Execute the plan
    # 1. Disable rules
    for r in plan["rules_to_disable"]:
        for s in store.rules["substitutions"]:
            if s["id"] == r["id"]:
                s["disabled"] = True
                s["disabled_why"] = f"keep_english({term})"

    # 2. Update exact rules
    for ec in plan["exact_changes"]:
        exact[ec["en"]] = ec["new"]

    # 3. Update glossary
    for gc in plan["glossary_changes"]:
        if gc["old"] is None:
            # Add new entry
            entry = {
                "en": gc["en"],
                "vi": gc["new"]["vi"],
                "short": gc["new"]["short"],
                "category": "user",
                "note": f"keep_english - {why}" if why else "keep_english",
                "source": "user",
                "locked": True,
                "updated": _now()
            }
            store.glossary.append(entry)
        else:
            # Update existing entry
            g = store.gl_by_en.get(gc["en"].lower())
            if g:
                g["vi"] = gc["new"]["vi"]
                g["short"] = gc["new"]["short"]
                g["locked"] = True
                g["source"] = "user"
                g["note"] = f"keep_english - {why}" if why else "keep_english"
                g["updated"] = _now()

    # 4. Update TM
    for tc in tm_changes:
        t = store.tm[tc["idx"]]
        t["vi"], t["migrated"], t["updated"] = tc["after"], f"keep_english:{term}", _now()

    # 5. Add/update keep_english entry
    existing_keep = next((k for k in store.keep if k.get("term") == term), None)
    keep_entry = {
        "term": term,
        "en_pattern": en_pattern,
        "vi_variants": vi_variants,
        "why": why,
        "added": existing_keep.get("added", _now()) if existing_keep else _now(),
        "updated": _now()
    }
    if existing_keep:
        existing_keep.clear()
        existing_keep.update(keep_entry)
    else:
        store.keep.append(keep_entry)

    # Save all files
    store.save_glossary()
    store.save_rules()
    store.save_tm()
    store.save_keep_english()
    store._index()

    _log(f"keep_english: **{term}** ({', '.join(vi_variants.keys())}) - {why}")

    return plan


def _phrase_diffs(wrong: str, right: str):
    """Extract replacement pairs and deletion patterns for learning."""
    a, b = wrong.split(), right.split()
    out = []
    drops = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [w.lower() for w in a], [w.lower() for w in b]).get_opcodes():
        if op == "replace" and 0 < i2 - i1 <= 4 and 0 < j2 - j1 <= 6:
            # one-syllable changes are too ambiguous in Vietnamese: widen to a 2-syllable phrase
            if i2 - i1 == 1 and j2 - j1 == 1:
                if i2 < len(a) and j2 < len(b) and a[i2] == b[j2]:
                    i2 += 1; j2 += 1
                elif i1 > 0 and j1 > 0 and a[i1 - 1] == b[j1 - 1]:
                    i1 -= 1; j1 -= 1
            w, r = " ".join(a[i1:i2]).strip(".,;:!?\"""()"), " ".join(b[j1:j2]).strip(".,;:!?\"""()")
            if w and r and w.lower() != r.lower():
                out.append((w, r))
        elif op == "delete" and 0 < i2 - i1 <= 3:
            # Capture deletions: words removed under width pressure
            deleted = " ".join(a[i1:i2]).strip(".,;:!?\"""()")
            # Include following word if available for context
            following = a[i2] if i2 < len(a) else ""
            if deleted and following:
                drops.append({"deleted": deleted, "following": following})
    return out, drops


def record_feedback(store: Store, en: str, wrong: str, right: str, reason: str = "", project: str = "",
                    always: bool = False, layout: dict | None = None) -> dict:
    """Log a user correction, update translation memory, and queue phrase-level rule candidates."""
    wrong, right = nfc(wrong), nfc(right)
    pairs, drops = _phrase_diffs(wrong, right)

    # Extract keep_english candidates: pairs where right side is English and in EN
    keep_english_candidates = []
    en_lower = en.lower()
    for w_wrong, w_right in pairs:
        # Check if right side consists of English words that appear in EN
        en_words = set(re.findall(r"[a-z]{2,}", en_lower))
        right_words = set(re.findall(r"[a-z]{2,}", w_right.lower()))
        if right_words and right_words.issubset(en_words):
            # This is a candidate for keep_english
            keep_english_candidates.append({"term": w_right, "vi_variant": w_wrong})

    fb = {"time": _now(), "en": en, "wrong": wrong, "right": right, "reason": reason, "project": project,
          "always": always, "phrases": pairs, "drops": drops}
    _append("feedback.jsonl", fb)
    store.feedback.append(fb)
    remember_translation(store, en, right, project, layout)
    _log(f"Sửa: `{wrong}` → `{right}`" + (f" - {reason}" if reason else ""))
    promoted = learn(store, min_count=1 if always else 2)["promoted"] if pairs or drops else []
    return {
        "logged": True,
        "phrase_candidates": pairs,
        "promoted_now": promoted,
        "keep_english_candidates": keep_english_candidates
    }


def learn(store: Store, min_count: int = 2, dry_run: bool = False) -> dict:
    """Promote corrections seen >= min_count times (or marked always) into substitution rules."""
    cnt = Counter()
    always = set()
    for fb in store.feedback:
        for w, r in fb.get("phrases", []):
            cnt[(w, r)] += 1
            if fb.get("always"):
                always.add((w, r))
    existing = {(s.get("learned_from") or "") for s in store.rules["substitutions"]}
    conflicts = Counter(w for (w, _r) in cnt)
    promoted, skipped = [], []
    for (w, r), n in cnt.most_common():
        if n < min_count and (w, r) not in always:
            continue
        sig = f"{w}→{r}"
        if sig in existing:
            continue
        rivals = [rr for (ww, rr) in cnt if ww == w and rr != r]
        if conflicts[w] > 1 and rivals and cnt[(w, r)] <= max(cnt[(w, rr)] for rr in rivals):
            skipped.append({"phrase": w, "reason": "mâu thuẫn giữa các lần sửa", "variants": [r] + rivals})
            continue
        rule = {"id": f"L{len(store.rules['substitutions']):03d}", "pattern": r"(?<!\w)" + re.escape(w) + r"(?!\w)", "replace": r,
                "fallback": None, "source": "learned", "learned_from": sig, "count": n, "hits": 0, "added": _now()}
        eng = re.findall(r"[A-Za-z]{2,}", r)
        if eng and not re.search(r"[^\x00-\x7f]", r):  # kept-English phrase: only where the source says it
            rule["en_requires"] = r"(?i)\b" + r"\s*".join(map(re.escape, eng)) + r"\b"
        promoted.append(rule)
        if not dry_run:
            store.rules["substitutions"].append(rule)
            _log(f"Tự học quy tắc mới `{w}` → `{r}` (gặp {n} lần)")
    # Dropped words (width-driven shortening): identity normally, shortened only under width pressure (level-1 fallback)
    dcnt, dalways = Counter(), set()
    for fb in store.feedback:
        for d in fb.get("drops", []):
            key = (d["deleted"], d["following"])
            dcnt[key] += 1
            if fb.get("always"):
                dalways.add(key)
    for (deleted, following), n in dcnt.items():
        if not following or (n < min_count and (deleted, following) not in dalways):
            continue
        sig = f"{deleted} {following}→{following}"
        if sig in existing or any(p.get("learned_from") == sig for p in promoted):
            continue
        rule = {"id": f"L{len(store.rules['substitutions']) + len(promoted):03d}",
                "pattern": r"(?i)(?<!\w)" + re.escape(f"{deleted} {following}") + r"(?!\w)", "replace": r"\g<0>",
                "fallback": following.lower(), "source": "learned", "learned_from": sig, "note": "chỉ áp khi tràn khung",
                "count": n, "hits": 0, "added": _now()}
        promoted.append(rule)
        if not dry_run:
            store.rules["substitutions"].append(rule)
            _log(f"Tự học rút gọn khi tràn: bỏ `{deleted}` trước `{following}`")
    if promoted and not dry_run:
        store.save_rules(); store._index()
    return {"promoted": promoted, "skipped": skipped, "pending": [{"phrase": f"{w}→{r}", "count": n} for (w, r), n in cnt.items()
                                                                   if n < min_count and (w, r) not in always]}


def review_rules(store: Store) -> dict:
    """Self-review: unused learned rules, rules that contradict the glossary, glossary conflicts."""
    unused = [s for s in store.rules["substitutions"] if s.get("source") == "learned" and not s.get("hits")]
    gl_conf = []
    seen = {}
    for g in store.glossary:
        k = g["en"].lower()
        if k in seen and seen[k] != g["vi"]:
            gl_conf.append(g["en"])
        seen[k] = g["vi"]
    banned_hits = []
    for b in store.rules.get("banned", []):
        rx = re.compile(b["pattern"])
        for g in store.glossary:
            if g.get("locked") and rx.search(g["vi"]):
                banned_hits.append({"term": g["en"], "vi": g["vi"], "banned": b["pattern"]})
    return {"learned_rules_never_used": [{"id": s["id"], "rule": s.get("learned_from")} for s in unused],
            "glossary_duplicates": gl_conf, "locked_terms_hit_banned_pattern": banned_hits,
            "feedback_count": len(store.feedback), "rules": len(store.rules["substitutions"]), "terms": len(store.glossary), "tm": len(store.tm)}


def disable_rule(store: Store, rule_id: str, why: str = "") -> dict:
    for s in store.rules["substitutions"]:
        if s["id"] == rule_id:
            s["disabled"] = True; s["disabled_why"] = why
            store.save_rules(); store._index()
            _log(f"Tắt quy tắc {rule_id} - {why}")
            return {"disabled": rule_id}
    return {"error": f"không có quy tắc {rule_id}"}


def commit_memory(message: str = "Cập nhật bộ nhớ dịch") -> dict:
    """git-commit the data dir (its own repo, or the enclosing one) so every learned change is reversible."""
    try:
        subprocess.run(["git", "-C", str(DATA), "add", "-A", "."], check=True, capture_output=True)
        r = subprocess.run(["git", "-C", str(DATA), "commit", "-m", message, "--", "."], capture_output=True, text=True)
        return {"ok": r.returncode == 0, "output": (r.stdout or r.stderr).strip()[-500:]}
    except Exception as e:  # git missing or not a repo
        return {"ok": False, "output": str(e)}
