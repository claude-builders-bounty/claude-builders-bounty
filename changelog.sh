#!/usr/bin/env bash
# Structured CHANGELOG Generator from Git History (Keep a Changelog 1.1.0 standard)

set -e

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
UNTIL_TAG="HEAD"

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --output|-o) OUTPUT_FILE="$2"; shift ;;
    --since|-s) SINCE_TAG="$2"; shift ;;
    --until|-u) UNTIL_TAG="$2"; shift ;;
    *) echo "Unknown parameter: $1"; exit 1 ;;
  esac
  shift
done

# If no since tag provided, auto-detect latest tag
if [ -z "$SINCE_TAG" ]; then
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [ -n "$LATEST_TAG" ]; then
    SINCE_TAG="$LATEST_TAG"
  fi
fi

if [ -n "$SINCE_TAG" ]; then
  RANGE="$SINCE_TAG..$UNTIL_TAG"
  VERSION_HEADER="## [Unreleased] (since $SINCE_TAG) - $(date +"%Y-%m-%d")"
else
  RANGE="$UNTIL_TAG"
  VERSION_HEADER="## [Unreleased] - $(date +"%Y-%m-%d")"
fi

COMMITS=$(git log "$RANGE" --pretty=format:"%s (%h by %an)" 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
  echo "No git commits found for range: $RANGE"
  exit 0
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  if [[ "$line" =~ ^feat(\(.*\))?:\ (.*) ]]; then
    ADDED+=("- ${BASH_REMATCH[2]}")
  elif [[ "$line" =~ ^fix(\(.*\))?:\ (.*) ]]; then
    FIXED+=("- ${BASH_REMATCH[2]}")
  elif [[ "$line" =~ ^(refactor|perf|change)(\(.*\))?:\ (.*) ]]; then
    CHANGED+=("- ${BASH_REMATCH[3]}")
  elif [[ "$line" =~ ^(remove|delete|deprecate)(\(.*\))?:\ (.*) ]]; then
    REMOVED+=("- ${BASH_REMATCH[3]}")
  else
    OTHER+=("- $line")
  fi
done <<< "$COMMITS"

cat << EOL > "$OUTPUT_FILE"
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

$VERSION_HEADER

EOL

if [ ${#ADDED[@]} -gt 0 ]; then
  echo "### Added" >> "$OUTPUT_FILE"
  for item in "${ADDED[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
  echo "" >> "$OUTPUT_FILE"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
  echo "### Changed" >> "$OUTPUT_FILE"
  for item in "${CHANGED[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
  echo "" >> "$OUTPUT_FILE"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
  echo "### Fixed" >> "$OUTPUT_FILE"
  for item in "${FIXED[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
  echo "" >> "$OUTPUT_FILE"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
  echo "### Removed" >> "$OUTPUT_FILE"
  for item in "${REMOVED[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
  echo "" >> "$OUTPUT_FILE"
fi

if [ ${#OTHER[@]} -gt 0 ]; then
  echo "### Other Changes" >> "$OUTPUT_FILE"
  for item in "${OTHER[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
  echo "" >> "$OUTPUT_FILE"
fi

echo "✅ Successfully generated $OUTPUT_FILE from git history ($RANGE)."
