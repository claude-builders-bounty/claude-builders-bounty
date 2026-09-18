#!/usr/bin/env bash
# Generate Keep-a-Changelog sections from commits since the last git tag.
set -euo pipefail
REPO="${1:-.}"
cd "$REPO"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $REPO" >&2
  exit 1
fi
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER_NOTE="Changes since tag ${LAST_TAG}"
else
  RANGE="HEAD"
  HEADER_NOTE="All commits (no tags found)"
fi
TODAY="$(date -u +%Y-%m-%d)"
# Pass commit subjects via argv file to avoid stdin clash
SUBJ_FILE="$(mktemp)"
git log $RANGE --pretty=format:'%s' > "$SUBJ_FILE" || true
python3 - "$TODAY" "$HEADER_NOTE" "$SUBJ_FILE" <<'PY'
import re, sys
today, header_note, path = sys.argv[1], sys.argv[2], sys.argv[3]
subjects = [ln.rstrip("\n") for ln in open(path, encoding="utf-8") if ln.strip()]
added, fixed, changed, removed, other = [], [], [], [], []
prefix = re.compile(
    r"^(?P<type>feat|feature|fix|bugfix|add|added|change|changed|update|chore|refactor|remove|removed|delete|deleted)\s*:\s*(?P<body>.+)$",
    re.I,
)
kw_add = re.compile(r"\b(add|added|feat|feature|introduce)\b", re.I)
kw_fix = re.compile(r"\b(fix|fixed|bugfix)\b", re.I)
kw_rm = re.compile(r"\b(remove|removed|delete|deleted)\b", re.I)
kw_ch = re.compile(r"\b(change|changed|update|updated|refactor)\b", re.I)
type_map = {
    "feat": "added", "feature": "added", "add": "added", "added": "added",
    "fix": "fixed", "bugfix": "fixed",
    "change": "changed", "changed": "changed", "update": "changed", "chore": "changed", "refactor": "changed",
    "remove": "removed", "removed": "removed", "delete": "removed", "deleted": "removed",
}
for s in subjects:
    m = prefix.match(s)
    if m:
        bucket = type_map[m.group("type").lower()]
        text = m.group("body").strip()
    elif kw_add.search(s):
        bucket, text = "added", s
    elif kw_fix.search(s):
        bucket, text = "fixed", s
    elif kw_rm.search(s):
        bucket, text = "removed", s
    elif kw_ch.search(s):
        bucket, text = "changed", s
    else:
        bucket, text = "other", s
    {"added": added, "fixed": fixed, "changed": changed, "removed": removed, "other": other}[bucket].append(text)

def section(title, items):
    print(f"### {title}")
    if items:
        for i in items:
            print(f"- {i}")
    else:
        print("- _(none)_")
    print()

print("# Changelog\n")
print(f"## Unreleased ({today})\n")
print(f"_{header_note}_\n")
section("Added", added)
section("Fixed", fixed)
section("Changed", changed)
section("Removed", removed)
if other:
    section("Other", other)
PY
rm -f "$SUBJ_FILE"
