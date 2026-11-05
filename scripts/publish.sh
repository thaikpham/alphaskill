#!/usr/bin/env bash
# Publish the vault: Obsidian → data → data-sample → api.alphacolorlab.com.
# Usage: scripts/publish.sh [--no-push]   (--no-push: import and export only)
set -euo pipefail
cd "$(dirname "$0")/.."

PUSH=true; [[ "${1:-}" == "--no-push" ]] && PUSH=false
: "${SONY_VN_DATA:?set SONY_VN_DATA to the private data checkout}"
DAY=$(date +%Y-%m-%d)

echo "▶ Obsidian import"
IMPORT=$(uv run python -m sony_alpha_viet.obsidian import --apply)
echo "$IMPORT" | uv run python -c '
import json, sys
out = json.load(sys.stdin)
conflicts = [c for part in out.values() if isinstance(part, dict) for c in part.get("conflicts", [])]
if conflicts:
    print("✗ conflicts:", *conflicts, sep="\n  "); sys.exit(1)
print("  terms:", len(out.get("terms", {}).get("changes", [])), "knowledge:", len(out.get("knowledge", {}).get("changes", [])))'

if $PUSH; then
  echo "▶ Push $SONY_VN_DATA"
  git -C "$SONY_VN_DATA" add -A knowledge
  git -C "$SONY_VN_DATA" commit -q -m "knowledge: $DAY" || echo "  nothing to commit"
  git -C "$SONY_VN_DATA" push
fi

echo "▶ Export data-sample"
BEFORE=$(find data-sample/knowledge -name '*.md' -exec basename {} .md \; | sort)
uv run python scripts/export_public_data.py "$SONY_VN_DATA" data-sample
AFTER=$(find data-sample/knowledge -name '*.md' -exec basename {} .md \; | sort)
# A title that disappeared is a dead /learn link unless the note kept it as an alias.
REMOVED=$(comm -23 <(echo "$BEFORE") <(echo "$AFTER"))
[[ -n "$REMOVED" ]] && echo "⚠ removed titles:" && echo "$REMOVED" | sed 's/^/  - /'
LOCAL=$(echo "$AFTER" | grep -c .)

if $PUSH; then
  echo "▶ Push data-sample"
  git add data-sample
  git commit -q -m "data-sample: knowledge $DAY" || echo "  nothing to commit"
  git push
  echo "▶ Wait for api.alphacolorlab.com (knowledge_count = $LOCAL)"
  for _ in $(seq 20); do
    REMOTE=$(curl -fsS https://api.alphacolorlab.com/v1 | uv run python -c 'import json,sys; print(json.load(sys.stdin)["data"].get("knowledge_count", 0))' || echo 0)
    [[ "$REMOTE" == "$LOCAL" ]] && { echo "✓ live: $REMOTE notes"; exit 0; }
    echo "  api: $REMOTE"; sleep 15
  done
  echo "⚠ api still at $REMOTE after 5 min"; exit 1
fi
echo "✓ done (no push): $LOCAL notes in data-sample"
