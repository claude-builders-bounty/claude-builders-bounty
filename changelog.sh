#!/usr/bin/env bash
set -euo pipefail

# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--output CHANGELOG.md] [--from-tag TAG] [--to-tag TAG]
#                         [--exclude-categories TYPES] [--template FILE]

OUTPUT="CHANGELOG.md"
FROM_TAG=""
TO_TAG=""
EXCLUDE_CATEGORIES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)       OUTPUT="$2"; shift 2 ;;
    --from-tag)     FROM_TAG="$2"; shift 2 ;;
    --to-tag)       TO_TAG="$2"; shift 2 ;;
    --exclude-categories) EXCLUDE_CATEGORIES="$2"; shift 2 ;;
    --template)     shift 2 ;; # reserved for custom templates
    --help|-h)      echo "Usage: bash changelog.sh [--output FILE] [--from-tag TAG] [--to-tag TAG] [--exclude-categories TYPES]"; exit 0 ;;
    *)              echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ ! -d .git ]; then
  echo "Error: must be run from a git repository root"
  exit 1
fi

# Determine version range
TAGS=$(git tag -l --sort=-v:refname 2>/dev/null || true)
if [ -z "$TAGS" ]; then
  # No tags — get all commits
  RANGE=""
  VERSION="0.1.0"
  PREV_DATE=""
else
  LATEST_TAG=$(echo "$TAGS" | head -1)
  if [ -n "$FROM_TAG" ]; then
    FROM_REF="$FROM_TAG"
  else
    FROM_REF=$(echo "$TAGS" | sed -n '2p')  # second latest
  fi
  if [ -n "$TO_TAG" ]; then
    TO_REF="$TO_TAG"
    VERSION="$TO_TAG"
  else
    TO_REF="$LATEST_TAG"
    VERSION="$LATEST_TAG"
  fi

  if [ -n "$FROM_REF" ]; then
    RANGE="${FROM_REF}..${TO_REF}"
  else
    RANGE="${TO_REF}"
  fi
  PREV_DATE=$(git log -1 --format="%ai" "$FROM_REF" 2>/dev/null || echo "")
fi

# Get commit log
COMMITS=$(git log --pretty=format:"%H||%s||%ai||%an" --no-merges $RANGE 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
  echo "No commits found in range."
  exit 0
fi

# Categorize commits
declare -A CATEGORIES
CATEGORIES["Added"]=""
CATEGORIES["Fixed"]=""
CATEGORIES["Changed"]=""
CATEGORIES["Removed"]=""
CATEGORIES["Deprecated"]=""
CATEGORIES["Security"]=""
CATEGORIES["Documentation"]=""
CATEGORIES["Other"]=""

DATE=""

while IFS= read -r LINE; do
  if [ -z "$LINE" ]; then continue; fi
  HASH="${LINE%%||*}"
  REST="${LINE#*||}"
  SUBJECT="${REST%%||*}"
  REST2="${REST#*||}"
  COMMIT_DATE="${REST2%%||*}"
  AUTHOR="${REST2##*||}"

  # Extract conventional commit type
  TYPE=$(echo "$SUBJECT" | sed -n 's/^\([a-z_]*\)[(!:].*/\1/p')
  DESCRIPTION=$(echo "$SUBJECT" | sed 's/^[a-z_]*\([!:]\)/\1/' | sed 's/^[!:][[:space:]]*//')

  if [ -z "$DESCRIPTION" ]; then
    DESCRIPTION="$SUBJECT"
    TYPE="other"
  fi

  # Map type to category
  case "$TYPE" in
    feat)          CAT="Added" ;;
    fix)           CAT="Fixed" ;;
    refactor|perf) CAT="Changed" ;;
    style)         CAT="Changed" ;;
    deprecat)      CAT="Deprecated" ;;
    remove|rem)    CAT="Removed" ;;
    sec|security)  CAT="Security" ;;
    docs|doc)      CAT="Documentation" ;;
    test|chore|build|ci|other) CAT="Other" ;;
    *)             CAT="Other" ;;
  esac

  SHORT_HASH="${HASH:0:7}"
  ENTRY="- ${DESCRIPTION} (${SHORT_HASH})"
  CATEGORIES["$CAT"]="${CATEGORIES[$CAT]}${ENTRY}\n"
  DATE="${COMMIT_DATE%% *}"
done <<< "$COMMITS"

# Generate date string
RELEASE_DATE="${DATE:-$(date +%Y-%m-%d)}"

# Build CHANGELOG
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
  echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
  echo ""
  echo "## [${VERSION}] — ${RELEASE_DATE}"
  echo ""

  # Build exclusion regex
  EXCLUDE_PATTERN=""
  if [ -n "$EXCLUDE_CATEGORIES" ]; then
    EXCLUDE_PATTERN="^($(echo "$EXCLUDE_CATEGORIES" | tr ',' '|'))$"
  fi

  for CAT in "Added" "Fixed" "Changed" "Deprecated" "Removed" "Security" "Documentation" "Other"; do
    if echo "$CAT" | grep -qE "$EXCLUDE_PATTERN" 2>/dev/null; then
      continue
    fi
    ENTRIES="${CATEGORIES[$CAT]}"
    if [ -n "$ENTRIES" ]; then
      echo "### ${CAT}"
      echo -e "$ENTRIES" | sed '/^$/d'
      echo ""
    fi
  done

  # Add comparison link if we have tags
  if [ -n "$VERSION" ] && [ -n "$FROM_REF" ] && [ "$FROM_REF" != "$VERSION" ]; then
    echo "[${VERSION}]: https://github.com/$(git config --get remote.origin.url 2>/dev/null | sed 's/.*:\(.*\)\.git/\1/')/compare/${FROM_REF}...${VERSION}"
  fi
} > "$OUTPUT"

echo "✓ Generated $OUTPUT ($(grep -c '^-' "$OUTPUT" || true) entries)"
