#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--all] [--since "2025-01-01"] [--tag v1.0.0] [--output CHANGELOG.md]
#
# By default, generates changelog from the latest git tag to HEAD.
set -euo pipefail

# --- Config ---
OUTPUT="CHANGELOG.md"
SINCE=""
TAG=""
ALL=false
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

# --- Parse Args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)      ALL=true; shift ;;
    --since)    SINCE="$2"; shift 2 ;;
    --tag)      TAG="$2"; shift 2 ;;
    --output)   OUTPUT="$2"; shift 2 ;;
    --help|-h)  echo "Usage: bash changelog.sh [--all] [--since DATE] [--tag TAG] [--output FILE]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# --- Determine range ---
cd "$REPO_ROOT"

if [[ "$ALL" == true ]]; then
  RANGE="HEAD"
elif [[ -n "$TAG" ]]; then
  RANGE="${TAG}..HEAD"
elif [[ -n "$SINCE" ]]; then
  RANGE="--since='$SINCE' HEAD"
else
  # Find latest tag
  LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
  if [[ -n "$LATEST_TAG" ]]; then
    RANGE="${LATEST_TAG}..HEAD"
  else
    RANGE="HEAD"
  fi
fi

# --- Fetch commits ---
if [[ "$ALL" == true ]]; then
  COMMITS="$(git log --pretty=format:"%s|%h|%ad" --date=short HEAD 2>/dev/null || true)"
elif [[ -n "$SINCE" ]]; then
  COMMITS="$(git log --pretty=format:"%s|%h|%ad" --date=short --since="$SINCE" HEAD 2>/dev/null || true)"
else
  COMMITS="$(git log --pretty=format:"%s|%h|%ad" --date=short $RANGE 2>/dev/null || true)"
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range: $RANGE"
  exit 0
fi

# --- Categorize ---
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
  MSG="$(echo "$line" | cut -d'|' -f1)"
  HASH="$(echo "$line" | cut -d'|' -f2)"
  DATE="$(echo "$line" | cut -d'|' -f3)"

  # Normalize: lowercase for matching
  LOWER_MSG="$(echo "$MSG" | tr '[:upper:]' '[:lower:]')"

  if echo "$LOWER_MSG" | grep -qE '^(add|feat|new|implement|introduce|create|support)'; then
    ADDED="${ADDED}- ${MSG} (${HASH}, ${DATE})\n"
  elif echo "$LOWER_MSG" | grep -qE '^(fix|bug|patch|resolve|correct|repair)'; then
    FIXED="${FIXED}- ${MSG} (${HASH}, ${DATE})\n"
  elif echo "$LOWER_MSG" | grep -qE '^(change|update|refactor|improve|enhance|modify|upgrade|bump)'; then
    CHANGED="${CHANGED}- ${MSG} (${HASH}, ${DATE})\n"
  elif echo "$LOWER_MSG" | grep -qE '^(remove|delete|drop|deprecate|clean)'; then
    REMOVED="${REMOVED}- ${MSG} (${HASH}, ${DATE})\n"
  else
    OTHER="${OTHER}- ${MSG} (${HASH}, ${DATE})\n"
  fi
done <<< "$COMMITS"

# --- Generate output ---
TODAY="$(date +%Y-%m-%d)"
if [[ "$ALL" == true ]]; then
  VERSION="All Changes"
elif [[ -n "$TAG" ]]; then
  VERSION="$TAG → $(git rev-parse --short HEAD)"
else
  LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
  if [[ -n "$LATEST_TAG" ]]; then
    VERSION="${LATEST_TAG} → $(git rev-parse --short HEAD)"
  else
    VERSION="Initial"
  fi
fi

cat > "$OUTPUT" << HEADER
# Changelog

All notable changes to this project will be documented in this file.

Generated on ${TODAY}.

---

## [${VERSION}] (${TODAY})

HEADER

if [[ -n "$ADDED" ]]; then
  printf "### Added\n\n${ADDED}\n" >> "$OUTPUT"
fi

if [[ -n "$FIXED" ]]; then
  printf "### Fixed\n\n${FIXED}\n" >> "$OUTPUT"
fi

if [[ -n "$CHANGED" ]]; then
  printf "### Changed\n\n${CHANGED}\n" >> "$OUTPUT"
fi

if [[ -n "$REMOVED" ]]; then
  printf "### Removed\n\n${REMOVED}\n" >> "$OUTPUT"
fi

if [[ -n "$OTHER" ]]; then
  printf "### Other\n\n${OTHER}\n" >> "$OUTPUT"
fi

COUNT="$(echo "$COMMITS" | wc -l | tr -d ' ')"
echo "✅ Generated ${OUTPUT} with ${COUNT} commits (${VERSION})"
