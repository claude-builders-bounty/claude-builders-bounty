#!/usr/bin/env bash
# changelog.sh - Generate CHANGELOG.md from git history
# Supports conventional commits, Keep a Changelog format
# Usage: ./changelog.sh [--stdout] [--since=<tag>]

set -e

OUTPUT_FILE="CHANGELOG.md"
USE_STDOUT=false
SINCE_TAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --stdout)
      USE_STDOUT=true
      shift
      ;;
    --since=*)
      SINCE_TAG="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Determine commit range
if [ -n "$SINCE_TAG" ]; then
  RANGE="$SINCE_TAG..HEAD"
elif git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG=$(git describe --tags --abbrev=0)
  RANGE="$LAST_TAG..HEAD"
else
  RANGE=""
fi

# Get commits
if [ -n "$RANGE" ]; then
  COMMITS=$(git log "$RANGE" --pretty=format:"%h|%s" --no-merges)
else
  COMMITS=$(git log --pretty=format:"%h|%s" --no-merges)
fi

# Categorize commits
declare -A CATEGORIES
CATEGORIES[Added]=""
CATEGORIES[Fixed]=""
CATEGORIES[Changed]=""
CATEGORIES[Removed]=""
CATEGORIES[Other]=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  HASH="${line%%|*}"
  MSG="${line#*|}"
  
  # Determine category
  category="Other"
  case "$MSG" in
    feat:*|feat\(*) category="Added" ;;
    fix:*|fix\(*)   category="Fixed" ;;
    refactor:*|perf:*|style:*|docs:*|test:*|chore:*|ci:*|build:*) category="Changed" ;;
    *BREAKING*|*breaking*) category="Removed" ;;
  esac
  
  CATEGORIES[$category]+="- $MSG ($HASH)"$'\n'
done <<< "$COMMITS"

# Generate output
OUTPUT="# Changelog"$'\n\n'
OUTPUT+="All notable changes to this project will be documented in this file."$'\n\n'
OUTPUT+="The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"$'\n'
OUTPUT+="and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."$'\n\n'

if [ -n "$RANGE" ]; then
  OUTPUT+="## [$LAST_TAG] - $(date +%Y-%m-%d)"$'\n\n'
else
  OUTPUT+="## [Unreleased] - $(date +%Y-%m-%d)"$'\n\n'
fi

for cat in Added Fixed Changed Removed Other; do
  if [ -n "${CATEGORIES[$cat]}" ]; then
    OUTPUT+="### $cat"$'\n\n'
    OUTPUT+="${CATEGORIES[$cat]}"$'\n'
  fi
done

# Output
if [ "$USE_STDOUT" = true ]; then
  echo "$OUTPUT"
else
  echo "$OUTPUT" > "$OUTPUT_FILE"
  echo "✓ Generated $OUTPUT_FILE"
fi
