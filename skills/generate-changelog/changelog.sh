#!/usr/bin/env bash
# generate-changelog — create a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <ref>]

set -o pipefail

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
SINCE="${2:-$LAST_TAG}"

# Category keywords mapped to their section headers
CATEGORIES=(
  "Added:add:feature:feat:new:created:implement"
  "Fixed:fix:bug:patch:hotfix:correct:resolve"
  "Changed:change:update:refactor:migrate:bump:improve"
  "Removed:remove:delete:deprecate:drop:cleanup"
)

CHANGELOG="CHANGELOG.md"
DATE=$(date +%Y-%m-%d)
NEW_VERSION=$(date +%Y.%m.%d)

# Gather commits and categorize them
declare -A SECTIONS
for cat in "${CATEGORIES[@]}"; do
  HEADER="${cat%%:*}"
  SECTIONS["$HEADER"]=""
  PATTERNS="${cat#*:}"
  IFS=':' read -ra KW <<< "$PATTERNS"
  for kw in "${KW[@]}"; do
    while IFS= read -r line; do
      commit_msg=$(echo "$line" | sed 's/^[a-f0-9]\{7,\} //')
      SECTIONS["$HEADER"]+="  - $commit_msg"$'\n'
    done < <(git log "$SINCE"..HEAD --oneline --grep="$kw" -i 2>/dev/null || true)
  done
done

# Deduplicate
for cat in "${!SECTIONS[@]}"; do
  SECTIONS["$cat"]=$(echo "${SECTIONS[$cat]}" | sort -u)
done

# Generate the file
{
  echo "# Changelog"
  echo ""
  echo "## [$NEW_VERSION] - $DATE"
  echo ""

  for HEADER in Added Fixed Changed Removed; do
    content="${SECTIONS[$HEADER]}"
    content="$(echo "$content" | sed '/^$/d')"
    if [ -n "$content" ]; then
      echo "### $HEADER"
      echo ""
      echo "$content"
      echo ""
    fi
  done
} > "$CHANGELOG"

echo "✅ Generated $CHANGELOG ($NEW_VERSION)"
