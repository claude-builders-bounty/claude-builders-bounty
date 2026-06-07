#!/usr/bin/env bash
set -euo pipefail
OUTPUT="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE="${LAST_TAG:+$LAST_TAG..}HEAD"
echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
for TYPE in "feat:Features" "fix:Bug Fixes" "docs:Documentation" "chore:Maintenance"; do
  PREFIX="${TYPE%%:*}"
  SECTION="${TYPE##*:}"
  git log "$RANGE" --grep="^$PREFIX" --pretty=format:"- %s (%an)" 2>/dev/null >> "$OUTPUT"
  [ -s "$OUTPUT" ] && echo "" >> "$OUTPUT"
done
echo "✅ Generated $OUTPUT"