#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
TAG="${2:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}"

if [ -z "$TAG" ]; then
  echo "No tag found. Use --tag to specify one."
  exit 1
fi

NOW=$(date -u +%Y-%m-%d)
VERSION="${TAG#v}"

cat > "$OUTPUT" << HEADER
# Changelog

## [${VERSION}] - ${NOW}

HEADER

# Group commits by category
added=$(git log "$TAG..HEAD" --oneline --grep="^feat\|^feature\|^add" --no-merges 2>/dev/null || true)
fixed=$(git log "$TAG..HEAD" --oneline --grep="^fix\|^bugfix\|^bug fix\|^hotfix" --no-merges 2>/dev/null || true)
changed=$(git log "$TAG..HEAD" --oneline --grep="^refactor\|^update\|^bump\|^chore\|^perf" --no-merges 2>/dev/null || true)
removed=$(git log "$TAG..HEAD" --oneline --grep="^remove\|^deprecat" --no-merges 2>/dev/null || true)

write_section() {
  local title="$1"
  local log="$2"
  if [ -n "$log" ]; then
    echo "" >> "$OUTPUT"
    echo "### ${title}" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$log" | while read -r line; do
      commit_hash="${line%% *}"
      commit_msg="${line#* }"
      echo "- ${commit_msg} (${commit_hash})" >> "$OUTPUT"
    done
  fi
}

write_section "Added" "$added"
write_section "Fixed" "$fixed"
write_section "Changed" "$changed"
write_section "Removed" "$removed"

echo "Generated $OUTPUT"
