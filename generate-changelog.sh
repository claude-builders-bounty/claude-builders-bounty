#!/usr/bin/env bash
set -euo pipefail

# generate-changelog.sh — Generate a CHANGELOG.md from git history
# Uses conventional commit prefixes to auto-categorize entries.
# No external dependencies — pure bash + git.

OUTPUT="CHANGELOG.md"
VERSION_OVERRIDE="${1:-}"

# --- Determine range ---
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
  RANGE=""
  FROM_DESC="the beginning"
else
  RANGE="${LAST_TAG}..HEAD"
  FROM_DESC="$LAST_TAG"
fi

END_DATE=$(date +%Y-%m-%d)

# --- Determine version label ---
if [ -n "$VERSION_OVERRIDE" ]; then
  VERSION_LABEL="$VERSION_OVERRIDE"
else
  VERSION_LABEL="Unreleased"
fi

# --- Collect commits ---
if [ -z "$RANGE" ]; then
  COMMITS=$(git log --format='%h|||%s' --reverse 2>/dev/null || echo "")
else
  COMMITS=$(git log --format='%h|||%s' --reverse "$RANGE" 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
  echo "No commits found since ${FROM_DESC}. Nothing to generate."
  exit 0
fi

# --- Category buckets ---
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# --- Categorize each commit ---
while IFS= read -r line; do
  [ -z "$line" ] && continue

  HASH=$(echo "$line" | cut -d'|' -f1)
  SUBJECT=$(echo "$line" | sed 's/^[^|]*|||//')

  # Extract type, optional scope, and description from conventional commit format
  if echo "$SUBJECT" | grep -qE '^[a-zA-Z]+(\([^)]*\))?:'; then
    TYPE=$(echo "$SUBJECT" | sed -E 's/^([a-zA-Z]+)(\([^)]*\))?\s*:.*/\1/' | tr '[:upper:]' '[:lower:]')
    SCOPE=$(echo "$SUBJECT" | sed -nE 's/^[a-zA-Z]+\(([^)]*)\)\s*:.*/\1/p')
    DESC=$(echo "$SUBJECT" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?\s*:\s*//')
  else
    TYPE=""
    DESC="$SUBJECT"
    SCOPE=""
  fi

  # Build bullet text with optional scope
  if [ -n "$SCOPE" ]; then
    BULLET="- **${SCOPE}**: ${DESC} (\`${HASH}\`)"
  else
    BULLET="- ${DESC} (\`${HASH}\`)"
  fi

  # Route to category
  case "$TYPE" in
    feat|feature|add)
      ADDED="${ADDED}${BULLET}\n"
      ;;
    fix|bugfix|patch)
      FIXED="${FIXED}${BULLET}\n"
      ;;
    refactor|change|update|improve)
      CHANGED="${CHANGED}${BULLET}\n"
      ;;
    remove|delete|drop)
      REMOVED="${REMOVED}${BULLET}\n"
      ;;
    *)
      OTHER="${OTHER}${BULLET}\n"
      ;;
  esac
done <<< "$COMMITS"

# --- Write CHANGELOG.md ---
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
  echo ""
  echo "## [${VERSION_LABEL}] - ${END_DATE}"
  echo ""

  if [ -n "$ADDED" ]; then
    echo "### Added"
    echo ""
    echo -e "${ADDED}"
  fi

  if [ -n "$FIXED" ]; then
    echo "### Fixed"
    echo ""
    echo -e "${FIXED}"
  fi

  if [ -n "$CHANGED" ]; then
    echo "### Changed"
    echo ""
    echo -e "${CHANGED}"
  fi

  if [ -n "$REMOVED" ]; then
    echo "### Removed"
    echo ""
    echo -e "${REMOVED}"
  fi

  if [ -n "$OTHER" ]; then
    echo "### Other"
    echo ""
    echo -e "${OTHER}"
  fi
} > "$OUTPUT"

echo "✅ Generated ${OUTPUT} with changes since ${FROM_DESC} (as of ${END_DATE})"
echo ""
cat "$OUTPUT"
