#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [since_tag] [output_file]
#   Without args: uses the latest git tag as starting point
#   With one arg:  custom starting tag or commit ref
#   With two args: custom tag + custom output path

set -euo pipefail

SINCE="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"
OUTPUT="${2:-CHANGELOG.md}"

if [ -z "$SINCE" ]; then
  echo "⚠️  No git tags found. Using first commit as starting point."
  SINCE=$(git rev-list --max-parents=0 HEAD)
fi

echo "📝 Generating changelog from $SINCE to HEAD..."

# Get today's date
TODAY=$(date +%Y-%m-%d)

# Get version from latest tag or use "Unreleased"
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")

# Collect commits, filter merges
COMMITS=$(git log "${SINCE}..HEAD" --no-merges --pretty=format:"%s" 2>/dev/null)

if [ -z "$COMMITS" ]; then
  echo "⚠️  No commits found since $SINCE"
  COMMITS=$(git log --no-merges --pretty=format:"%s" -20)
  SINCE="first commit"
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  # Skip empty lines
  [ -z "$line" ] && continue
  
  # Detect type from conventional commit prefix or keyword
  msg_lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
  
  if echo "$msg_lower" | grep -qE '^(feat|add|added|implement|create|introduce|new)'; then
    ADDED="$ADDED- ${line#*: }\n"
  elif echo "$msg_lower" | grep -qE '^(fix|fixed|bug|resolve|patch|hotfix|correct)'; then
    FIXED="$FIXED- ${line#*: }\n"
  elif echo "$msg_lower" | grep -qE '^(remove|removed|delete|drop|deprecate)'; then
    REMOVED="$REMOVED- ${line#*: }\n"
  elif echo "$msg_lower" | grep -qE '^(chore|docs|style|refactor|perf|test|ci|build|revert)'; then
    CHANGED="$CHANGED- ${line#*: }\n"
  else
    # Uncategorized → Changed
    CHANGED="$CHANGED- $line\n"
  fi
done <<< "$COMMITS"

# Generate CHANGELOG
{
  echo "# Changelog"
  echo ""
  echo "## [$VERSION] - $TODAY"
  echo ""

  if [ -n "$ADDED" ]; then
    echo "### Added"
    echo -e "$ADDED"
  fi

  if [ -n "$FIXED" ]; then
    echo "### Fixed"
    echo -e "$FIXED"
  fi

  if [ -n "$CHANGED" ]; then
    echo "### Changed"
    echo -e "$CHANGED"
  fi

  if [ -n "$REMOVED" ]; then
    echo "### Removed"
    echo -e "$REMOVED"
  fi
} > "$OUTPUT"

# Count entries
TOTAL=$(grep -c '^- ' "$OUTPUT" 2>/dev/null || echo 0)

echo "✅ Changelog written to $OUTPUT"
echo "   Version: $VERSION"
echo "   Commits: $(echo "$COMMITS" | wc -l | tr -d ' ')"
echo "   Entries: $TOTAL"
echo "   Added:   $( [ -n "$ADDED" ] && echo "$ADDED" | grep -c '^-' || echo 0 )"
echo "   Fixed:   $( [ -n "$FIXED" ] && echo "$FIXED" | grep -c '^-' || echo 0 )"
echo "   Changed: $( [ -n "$CHANGED" ] && echo "$CHANGED" | grep -c '^-' || echo 0 )"
echo "   Removed: $( [ -n "$REMOVED" ] && echo "$REMOVED" | grep -c '^-' || echo 0 )"
