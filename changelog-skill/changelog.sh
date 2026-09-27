#!/usr/bin/env bash
# changelog.sh — sinh CHANGELOG.md có cấu trúc từ git history (bash only, không deps).
#   bash changelog.sh [--since <tag>] [--out CHANGELOG.md] [--repo <dir>]
# Phân loại: Added / Fixed / Changed / Removed theo conventional-commit prefix.
set -euo pipefail

SINCE="" OUT="CHANGELOG.md" REPO="."
while [[ $# -gt 0 ]]; do case "$1" in
  --since) SINCE="$2"; shift 2;;
  --out) OUT="$2"; shift 2;;
  --repo) REPO="$2"; shift 2;;
  *) echo "dùng: bash changelog.sh [--since <tag>] [--out FILE] [--repo DIR]" >&2; exit 1;;
esac done

cd "$REPO"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "không phải git repo: $REPO" >&2; exit 1; }

if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi
RANGE="HEAD"; [[ -n "$SINCE" ]] && RANGE="$SINCE..HEAD"

LOG_TMP=$(mktemp)
git log $RANGE --pretty=format:'%s' 2>/dev/null > "$LOG_TMP" || true
N=$(grep -c . "$LOG_TMP" || true)
if [[ "$N" -eq 0 ]]; then echo "không có commit mới trong $RANGE" >&2; rm -f "$LOG_TMP"; exit 0; fi

added=(); fixed=(); changed=(); removed=()
while IFS= read -r s; do
  [[ -z "$s" ]] && continue
  low=$(echo "$s" | tr '[:upper:]' '[:lower:]')
  case "$low" in
    feat*|add*|new*|*" new "*) added+=("$s");;
    fix*|bug*|hotfix*|patch*) fixed+=("$s");;
    remove*|delete*|drop*|deprecat*) removed+=("$s");;
    *) changed+=("$s");;
  esac
done < "$LOG_TMP"
rm -f "$LOG_TMP"

print_sec() { # $1=name $2+=items via shift
  local name="$1"; shift
  echo "### $name"
  if [[ $# -eq 0 ]]; then echo "- (không có)"; else local i; for i in "$@"; do echo "- $i"; done; fi
  echo ""
}

set +u  # bash 3.2: mảng rỗng + set -u lỗi khi expand
{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] — từ ${SINCE:-khởi đầu} ($(date +%F), $N commits)"
  echo ""
  print_sec "Added" "${added[@]}"
  print_sec "Fixed" "${fixed[@]}"
  print_sec "Changed" "${changed[@]}"
  print_sec "Removed" "${removed[@]}"
} > "$OUT"
nA=${#added[@]}; nF=${#fixed[@]}; nC=${#changed[@]}; nR=${#removed[@]}
set -u
echo "ghi $((nA+nF+nC+nR)) commits (A:$nA F:$nF C:$nC R:$nR) -> $OUT"
