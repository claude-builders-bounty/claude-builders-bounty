#!/usr/bin/env bash
# Changlog generator — makes a pretty markdown log from git history
# Usage: bash changelog.sh [--since TAG] [--repo /path] [--output FILE]
set -euo pipefail

REPO="."
SINCE_TAG=""
OUTPUT="CHANGELOG.md"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Usage: $0 [--since TAG] [--repo PATH] [--output FILE]"; exit 1 ;;
  esac
done

cd "$REPO"

# Determine range
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
fi

echo "📋 Generating CHANGELOG since $SINCE_TAG..."
echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## $(date +%Y-%m-%d)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Categorize commits
for category in "Added:feat:✨" "Fixed:fix:🐛" "Changed:chore|refactor:🔧" "Removed:remove|delete:🗑️" "Security:security|fix.*security:🔒"; do
  label="${category%%:*}"
  rest="${category#*:}"
  patterns="${rest%:*}"
  emoji="${rest##*:}"
  
  commits=$(git log "$SINCE_TAG..HEAD" --oneline -E 2>/dev/null | grep -iE "$patterns" | head -50)
  if [[ -n "$commits" ]]; then
    echo "### $emoji $label" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    git log "$SINCE_TAG..HEAD" --format="  - %s (%h)" --grep="$patterns" -E 2>/dev/null | head -50 >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
done

# Uncategorized
others=$(git log "$SINCE_TAG..HEAD" --oneline --not --grep="feat\|fix\|chore\|remove\|delete\|security" -E 2>/dev/null | head -20)
if [[ -n "$others" ]]; then
  echo "### 📝 Other" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
  git log "$SINCE_TAG..HEAD" --format="  - %s (%h)" --not --grep="feat\|fix\|chore\|remove\|delete\|security" -E 2>/dev/null | head -20 >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

echo ""
echo "✅ Generated $OUTPUT ($(grep -c '^-' "$OUTPUT") commits)"
