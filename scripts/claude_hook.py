#!/usr/bin/env python3
"""Claude Code hook (.claude/settings.json).

PreToolUse(Bash): block `git commit`/`git push` while data files are staged, untracked-but-not-ignored or unpushed
in this code repo; data lives in its own repo (github.com/thaikpham/alphaskill-data, submodule `data/`).
PostToolUse(Edit|Write): rebuild portable/ after editing skills/sony-alpha-viet/.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = re.compile(r"(^|/)(tm|feedback)\.jsonl$|(^|/)LEARNING_LOG\.md$|(^|/)knowledge/|\.(pdf|docx?|xlsx?|epub)$", re.I)
PUBLIC = ("data-sample/", "portable/")


def git(*args):
    r = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.splitlines() if r.returncode == 0 else []


ev = json.loads(sys.stdin.read().strip() or "{}")
inp = ev.get("tool_input") or {}
if ev.get("hook_event_name") == "PreToolUse":
    if re.search(r"\bgit\b.*\b(commit|push)\b", inp.get("command", "")):
        files = git("diff", "--cached", "--name-only") + git("diff", "--name-only", "@{u}..HEAD")
        files += [line[3:].split(" -> ")[-1].strip('"') for line in git("status", "--porcelain", "-uall")]
        bad = sorted({f for f in files if PRIVATE.search(f) and not f.startswith(PUBLIC)})
        if bad:
            print("Blocked: data files belong in the data repo (alphaskill-data), not this code repo:\n  " + "\n  ".join(bad)
                  + "\nCommit them in data/ (the submodule) instead, or add them to .gitignore.", file=sys.stderr)
            sys.exit(2)
elif "/skills/sony-alpha-viet/" in inp.get("file_path", ""):
    r = subprocess.run([sys.executable, str(ROOT / "scripts/build_portable.py")], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout + r.stderr, file=sys.stderr)
        sys.exit(2)
