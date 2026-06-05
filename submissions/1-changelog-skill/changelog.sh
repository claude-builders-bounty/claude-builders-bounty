#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]

set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE="${2:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$SINCE" ]; then
  RANGE=""
  TITLE="All Commits"
else
  RANGE="${SINCE}..HEAD"
  TITLE="Changes since ${SINCE}"
fi

COMMITS=$(git log $RANGE --pretty=format:"%s" --no-merges 2>/dev/null || git log --pretty=format:"%s" --no-merges)
DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")

# Categorize
added=$(echo "$COMMITS" | grep -iE '^feat:|^add:|^new:' || true)
fixed=$(echo "$COMMITS" | grep -iE '^fix:|^bug:|^hotfix:|^patch:' || true)
changed=$(echo "$COMMITS" | grep -iE '^chore:|^refactor:|^perf:|^style:|^update:' || true)
removed=$(echo "$COMMITS" | grep -iE '^remove:|^revert:|^drop:|^delete:' || true)

cat > "$OUTPUT" << EOF
# Changelog

## [$VERSION] — $DATE

EOF

section() {
  local title="$1"
  local items="$2"
  if [ -n "$items" ]; then
    echo "### $title" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      clean=$(echo "$line" | sed -E 's/^(feat|fix|chore|refactor|perf|style|add|new|bug|hotfix|patch|remove|revert|drop|delete|update):\s*//i')
      echo "- $clean" >> "$OUTPUT"
    done <<< "$items"
    echo "" >> "$OUTPUT"
  fi
}

section "Added" "$added"
section "Fixed" "$fixed"
section "Changed" "$changed"
section "Removed" "$removed"

echo "✅ $OUTPUT generated with $(echo "$COMMITS" | wc -l) commits"
