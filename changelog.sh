#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history since the last tag.
# Usage: bash changelog.sh [version]          (write CHANGELOG.md)
#        DRY_RUN=1 bash changelog.sh [version] (print only, don't write)
set -euo pipefail

VERSION="${1:-Unreleased}"
TODAY=$(date +%Y-%m-%d)
CHANGELOG="CHANGELOG.md"

# Determine the "since" ref: last tag, or first commit if no tag
LAST_TAG=$(git tag --sort=-creatordate | head -1)
if [ -n "$LAST_TAG" ]; then
  SINCE="$LAST_TAG"
else
  SINCE=$(git rev-list --max-parents=0 HEAD)
fi

echo "📝 Generating changelog since: $SINCE → HEAD"

# Collect commits, skip merges
COMMITS=$(git log "${SINCE}..HEAD" --no-merges --pretty=format:'%s')

# Initialize categorization buckets
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  # Strip leading/trailing whitespace
  msg=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  # Categorize by Conventional Commits prefix
  if echo "$msg" | grep -qiE '^feat[(:]'; then
    ADDED+="- ${msg}\n"
  elif echo "$msg" | grep -qiE '^fix[(:]'; then
    FIXED+="- ${msg}\n"
  elif echo "$msg" | grep -qiE '^(revert|remove|drop)[(:]'; then
    REMOVED+="- ${msg}\n"
  elif echo "$msg" | grep -qiE '^(refactor|perf|style|chore|docs|test|ci|build)[(:]'; then
    CHANGED+="- ${msg}\n"
  else
    CHANGED+="- ${msg}\n"
  fi
done <<< "$COMMITS"

# Build the release block
RELEASE="## [${VERSION}] - ${TODAY}\n"

if [ -n "$ADDED" ]; then
  RELEASE+="\n### Added\n${ADDED}"
fi
if [ -n "$FIXED" ]; then
  RELEASE+="\n### Fixed\n${FIXED}"
fi
if [ -n "$CHANGED" ]; then
  RELEASE+="\n### Changed\n${CHANGED}"
fi
if [ -n "$REMOVED" ]; then
  RELEASE+="\n### Removed\n${REMOVED}"
fi

RELEASE+="\n"

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo -e "\n===== PREVIEW ====="
  echo -e "$RELEASE"
  echo "===================="
else
  if [ -f "$CHANGELOG" ]; then
    # Insert new release after the header line
    HEADER=$(head -1 "$CHANGELOG")
    BODY=$(tail -n +2 "$CHANGELOG")
    echo -e "$HEADER\n\n$RELEASE$BODY" > "$CHANGELOG"
  else
    echo -e "# Changelog\n\n$RELEASE" > "$CHANGELOG"
  fi
  echo "✅ Wrote $CHANGELOG"
fi
