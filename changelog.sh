#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--output CHANGELOG.md]

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_DIR="${2:-.}"
cd "$REPO_DIR" || exit 1

# Find the last tag, fall back to first commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
echo "Generating changelog since: $LAST_TAG"

# Initialize output
cat > "$OUTPUT" <<'EOF'
# Changelog

EOF

# Temp files for each category
for cat in Added Fixed Changed Removed; do
  : > "$OUTPUT.tmp.$cat"
done

# Process each commit
git log "$LAST_TAG..HEAD" --pretty=format:"%H||%s||%aN||%aI" --no-merges | while IFS= read -r line; do
  IFS="||" read -r hash subject author date <<< "$line"

  # Categorize based on conventional commits
  category="Changed"
  case "$subject" in
    feat:*|feature:*|add:*|new:*|implement:*) category="Added" ;;
    fix:*|bugfix:*|bug:*|hotfix:*|patch:*) category="Fixed" ;;
    remove:*|drop:*|delete:*|deprecate:*) category="Removed" ;;
    change:*|update:*|refactor:*|improve:*|bump:*|upgrade:*|migrate:*) category="Changed" ;;
  esac

  # Strip conventional commit prefix, truncate hash
  clean_subject=$(echo "$subject" | sed -E 's/^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert|add|remove|update|change|improve|bump|migrate)\([^)]*\)!?: *//' | sed -E 's/^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert|add|remove|update|change|improve|bump|migrate)!?: *//')
  echo "- $clean_subject (${hash:0:7})" >> "$OUTPUT.tmp.$category"
done

# Write categorized sections
for cat in Added Fixed Changed Removed; do
  if [[ -s "$OUTPUT.tmp.$cat" ]]; then
    echo "### $cat" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    sort "$OUTPUT.tmp.$cat" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    rm "$OUTPUT.tmp.$cat"
  fi
done

echo "Changelog written to $OUTPUT"
