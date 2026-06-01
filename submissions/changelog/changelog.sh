#!/usr/bin/env bash
# changelog.sh — 从 git 历史自动生成 CHANGELOG.md
# Usage: bash changelog.sh [since_tag] [output_file]
set -euo pipefail

SINCE="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"
OUTPUT="${2:-CHANGELOG.md}"
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

if [ -z "$SINCE" ]; then
  SINCE="$(git rev-list --max-parents=0 HEAD)"
fi

# 加空行防止最后一行丢失
{ git log "${SINCE}..HEAD" --pretty=format:"%s"; echo ""; } > "$TMP/commits"

while IFS= read -r msg; do
  [ -z "$msg" ] && continue
  case "$msg" in
    *[Aa]dd*|*[Ff]eat:*) echo "- $msg" >> "$TMP/added" ;;
    *[Ff]ix[:,\ ]*|*[Bb]ug[:,\ ]*) echo "- $msg" >> "$TMP/fixed" ;;
    *[Rr]emove*|*[Dd]elete*|*[Dd]rop*) echo "- $msg" >> "$TMP/removed" ;;
    *) echo "- $msg" >> "$TMP/changed" ;;
  esac
done < "$TMP/commits"

ver=$(git tag --points-at HEAD 2>/dev/null || git rev-parse --short HEAD)

{ echo "# Changelog"; echo ""; echo "## $ver"; echo ""; } > "$OUTPUT"

for cat in added fixed changed removed; do
  [ -f "$TMP/$cat" ] || continue
  name="${cat^}"
  { echo "### $name"; cat "$TMP/$cat"; echo ""; } >> "$OUTPUT"
done

echo "✅ $OUTPUT ($(wc -l < "$OUTPUT") lines)"