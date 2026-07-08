#!/usr/bin/env bash
set -euo pipefail
OUTPUT="${1:-CHANGELOG.md}"
SINCE=$(git tag --sort=-creatordate | head -1 2>/dev/null || echo "")
VERSION="${SINCE:-Unreleased}"
DATE=$(date +%Y-%m-%d)

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [$VERSION] - $DATE" >> "$OUTPUT"
echo "" >> "$OUTPUT"

A=""; F=""; C=""; R=""

while IFS= read -r msg; do
    msg=$(echo "$msg" | xargs)
    [[ -z "$msg" ]] && continue
    l=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    if echo "$l" | grep -qE '^(feat|add)[(: ]'; then A+="  - $msg"$'\n'
    elif echo "$l" | grep -qE '^(fix|bug|hotfix)[(: ]'; then F+="  - $msg"$'\n'
    elif echo "$l" | grep -qE '^(remove|drop|revert)[(: ]'; then R+="  - $msg"$'\n'
    else C+="  - $msg"$'\n'; fi
done < <(git log --max-count=50 --pretty=format:"%s")

[[ -n "$A" ]] && echo "### Added" >> "$OUTPUT" && echo "$A" >> "$OUTPUT"
[[ -n "$F" ]] && echo "### Fixed" >> "$OUTPUT" && echo "$F" >> "$OUTPUT"
[[ -n "$C" ]] && echo "### Changed" >> "$OUTPUT" && echo "$C" >> "$OUTPUT"
[[ -n "$R" ]] && echo "### Removed" >> "$OUTPUT" && echo "$R" >> "$OUTPUT"

echo "✅ $OUTPUT ($VERSION)"