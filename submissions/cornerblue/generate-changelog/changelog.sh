#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since the last tag.
# Usage: bash changelog.sh [output-file]
set -euo pipefail

OUT="${1:-CHANGELOG.md}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "error: not a git repository" >&2
  exit 1
}
cd "$ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${LAST_TAG}" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER_NOTE="Changes since \`${LAST_TAG}\`"
  LOG_ARGS=("${LAST_TAG}..HEAD")
else
  RANGE="HEAD"
  HEADER_NOTE="All commits (no tags found)"
  LOG_ARGS=("HEAD")
fi

TODAY="$(date -u +%Y-%m-%d)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

git log "${LOG_ARGS[@]}" --pretty=format:'%s' >"$TMP" || true

python3 - "$TMP" "$OUT" "$TODAY" "$HEADER_NOTE" "$RANGE" <<'PY'
import sys
from pathlib import Path

subjects = Path(sys.argv[1]).read_text(errors="replace").splitlines()
out_path = Path(sys.argv[2])
today = sys.argv[3]
header_note = sys.argv[4]
range_ = sys.argv[5]

added, fixed, changed, removed = [], [], [], []

def cat(line: str) -> str:
    low = line.lower().strip()
    # conventional commits
    import re
    m = re.match(r"^([a-z]+)(\([^)]*\))?(!)?:\s*", low)
    if m:
        t = m.group(1)
        if t in ("feat", "feature"):
            return "added"
        if t == "fix":
            return "fixed"
        if t in ("remove", "revert", "deprecate"):
            return "removed"
        if t in ("chore", "refactor", "perf", "docs", "style", "ci", "build", "test", "change", "update"):
            return "changed"
    if low.startswith(("add", "added", "create", "implement", "support", "feature")):
        return "added"
    if low.startswith(("fix", "fixed", "bug", "hotfix", "patch", "resolve", "repair")):
        return "fixed"
    if low.startswith(("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecate")):
        return "removed"
    if low.startswith(("chore", "refactor", "perf", "improve", "update", "change", "rename", "docs", "style", "ci", "build", "revert")):
        return "changed"
    return "changed"

for line in subjects:
    line = line.strip()
    if not line:
        continue
    bucket = cat(line)
    if bucket == "added":
        added.append(line)
    elif bucket == "fixed":
        fixed.append(line)
    elif bucket == "removed":
        removed.append(line)
    else:
        changed.append(line)

def section(title, items):
    lines = [f"### {title}", ""]
    if items:
        lines += [f"- {i}" for i in items]
    else:
        lines.append("- _(none)_")
    lines.append("")
    return lines

parts = [
    "# Changelog",
    "",
    f"## {today}",
    "",
    f"_{header_note}_",
    "",
]
parts += section("Added", added)
parts += section("Fixed", fixed)
parts += section("Changed", changed)
parts += section("Removed", removed)
out_path.write_text("\n".join(parts))
print(f"Wrote {out_path} ({header_note}, range={range_})")
PY
