#!/usr/bin/env bash
# changelog.sh — Pure Bash Keep-a-Changelog generator
set -euo pipefail

FROM_TAG=""
OUTPUT_FILE=""
DRY_RUN=false
VERSION_TITLE="Unreleased"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-tag) FROM_TAG="$2"; shift 2 ;;
    --output|-o) OUTPUT_FILE="$2"; shift 2 ;;
    --title) VERSION_TITLE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown parameter: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$FROM_TAG" ]; then
  FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -n "$FROM_TAG" ]; then
  GIT_RANGE="${FROM_TAG}..HEAD"
  TAG_INFO="since tag \`${FROM_TAG}\`"
else
  GIT_RANGE="HEAD"
  TAG_INFO="initial release"
fi

TODAY=$(date -u +%Y-%m-%d)

COMMITS=$(git log "$GIT_RANGE" --pretty=format:"%h%x1f%s%x1f%an" 2>/dev/null || echo "")
if [ -z "$COMMITS" ]; then
  echo "No commits found in range: $GIT_RANGE"
  exit 0
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
TOTAL_COUNT=0

while IFS=$'\x1f' read -r short_sha subject author; do
  [ -z "$short_sha" ] && continue
  TOTAL_COUNT=$((TOTAL_COUNT + 1))

  # Categorize by prefix
  if [[ "$subject" =~ ^(feat|feature|add|new)(\([^)]+\))?!?:?[[:space:]]*(.*) ]]; then
    desc="${BASH_REMATCH[3]}"
    [ -z "$desc" ] && desc="$subject"
    ADDED="${ADDED}- ${desc} (\`${short_sha}\`) — *${author}*"$'\n'
  elif [[ "$subject" =~ ^(fix|bug|hotfix|patch)(\([^)]+\))?!?:?[[:space:]]*(.*) ]]; then
    desc="${BASH_REMATCH[3]}"
    [ -z "$desc" ] && desc="$subject"
    FIXED="${FIXED}- ${desc} (\`${short_sha}\`) — *${author}*"$'\n'
  elif [[ "$subject" =~ ^(revert|remove|delete|deprecate)(\([^)]+\))?!?:?[[:space:]]*(.*) ]]; then
    desc="${BASH_REMATCH[3]}"
    [ -z "$desc" ] && desc="$subject"
    REMOVED="${REMOVED}- ${desc} (\`${short_sha}\`) — *${author}*"$'\n'
  else
    CHANGED="${CHANGED}- ${subject} (\`${short_sha}\`) — *${author}*"$'\n'
  fi
done <<< "$COMMITS"

MARKDOWN="## [${VERSION_TITLE}] — ${TODAY}
*${TOTAL_COUNT} commits ${TAG_INFO}*
"

if [ -n "$ADDED" ]; then
  MARKDOWN="${MARKDOWN}
### Added
${ADDED}"
fi

if [ -n "$FIXED" ]; then
  MARKDOWN="${MARKDOWN}
### Fixed
${FIXED}"
fi

if [ -n "$CHANGED" ]; then
  MARKDOWN="${MARKDOWN}
### Changed
${CHANGED}"
fi

if [ -n "$REMOVED" ]; then
  MARKDOWN="${MARKDOWN}
### Removed
${REMOVED}"
fi

if [ -n "$OUTPUT_FILE" ] && [ "$DRY_RUN" = false ]; then
  echo "$MARKDOWN" > "$OUTPUT_FILE"
  echo "Changelog written to $OUTPUT_FILE"
fi

echo "$MARKDOWN"
