#!/bin/bash
# Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [repo-path]

set -e

OUTPUT_FILE="CHANGELOG.md"

# Allow specifying a repo path as argument
if [ -n "$1" ]; then
  cd "$1"
fi

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  echo "No tags found. Using all commits."
  COMMITS=$(git log --pretty=format:"%h|%s|%an|%ad" --date=short 2>/dev/null || echo "")
else
  echo "Generating changelog since $LAST_TAG"
  COMMITS=$(git log "${LAST_TAG}..HEAD" --pretty=format:"%h|%s|%an|%ad" --date=short 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
  echo "No commits found."
  exit 0
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# Parse commits and categorize
while IFS='|' read -r hash subject author date; do
  # Strip leading/trailing whitespace from subject
  subject=$(echo "$subject" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  entry="- ${subject} (\`${hash}\`)"

  # Match prefix (case-insensitive via tolower trick)
  lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  case "$lower_subject" in
    feat:*|feat\(*\):*|add:*|added:*|new:*|feature:*)
      ADDED="${ADDED}${entry}\n"
      ;;
    fix:*|fix\(*\):*|fixed:*|bugfix:*|bugfix:*|hotfix:*|patch:*)
      FIXED="${FIXED}${entry}\n"
      ;;
    change:*|changed:*|update:*|updated:*|refactor:*|improve:*|improved:*|enhance:*|enhanced:*|chore:*|build:*|ci:*|perf:*|style:*)
      CHANGED="${CHANGED}${entry}\n"
      ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|deprecated:*)
      REMOVED="${REMOVED}${entry}\n"
      ;;
    docs:*|doc:*)
      CHANGED="${CHANGED}${entry}\n"
      ;;
    revert:*|reverted:*)
      CHANGED="${CHANGED}${entry}\n"
      ;;
    *)
      OTHER="${OTHER}${entry}\n"
      ;;
  esac
done <<< "$COMMITS"

# Helper: print section only if non-empty
print_section() {
  local title="$1"
  local content="$2"
  local cleaned
  cleaned=$(echo -e "$content" | sed '/^[[:space:]]*$/d')
  if [ -n "$cleaned" ]; then
    echo ""
    echo "### $title"
    echo ""
    echo -e "$cleaned"
  fi
}

# Build changelog
VERSION_LABEL="${LAST_TAG:-Initial Release}"
DATE=$(date +%Y-%m-%d)

{
  echo "# Changelog"
  echo ""
  echo "## [${VERSION_LABEL}] - ${DATE}"
  print_section "Added" "$ADDED"
  print_section "Fixed" "$FIXED"
  print_section "Changed" "$CHANGED"
  print_section "Removed" "$REMOVED"
  print_section "Other" "$OTHER"
} > "$OUTPUT_FILE"

echo "Changelog generated: $OUTPUT_FILE"
