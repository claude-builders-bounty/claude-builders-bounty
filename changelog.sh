#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
# Fetches commits since the last git tag, categorizes them, and writes CHANGELOG.md.
#
# Usage: bash changelog.sh [since-tag]
#   If no tag is given, uses the latest tag (git describe --tags).
set -euo pipefail

OUT="CHANGELOG.md"

# Determine the "since" ref: argument, else latest tag, else first commit.
if [ $# -ge 1 ]; then
  SINCE="$1"
else
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
fi

echo "Generating changelog since: ${SINCE}"

# Map conventional-commit prefixes to categories.
categorize() {
  local msg="$1"
  case "$msg" in
    feat*:|add*|Add*) echo "Added" ;;
    fix*:|Fix*) echo "Fixed" ;;
    refactor*|chore*|change*|Change*|update*|Update*|Bump*) echo "Changed" ;;
    remove*|Remove*|delete*|Delete*|Drop*) echo "Removed" ;;
    *) echo "Changed" ;;
  esac
}

# Build a temp file of categorized entries.
TMP=$(mktemp)
while IFS= read -r line; do
  hash="${line%% *}"
  subject="${line#* }"
  cat=$(categorize "$subject")
  printf '%s\t%s\t%s\n' "$cat" "$hash" "$subject" >> "$TMP"
done < <(git log "${SINCE}..HEAD" --pretty=format:"%h %s")

DATE=$(date +%Y-%m-%d)
{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] - ${DATE}"
  echo ""
  for section in Added Fixed Changed Removed; do
    entries=$(grep -F "$section"$'\t' "$TMP" | cut -f2,3 | sed 's/\t/ /' || true)
    if [ -n "$entries" ]; then
      echo "### ${section}"
      echo "$entries" | while IFS= read -r e; do
        [ -z "$e" ] && continue
        echo "- ${e}"
      done
      echo ""
    fi
  done
} > "$OUT"

rm -f "$TMP"
echo "Wrote ${OUT}"
