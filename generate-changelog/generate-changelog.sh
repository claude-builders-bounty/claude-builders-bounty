#!/usr/bin/env bash
# generate-changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [repo_path] [output_file]
# Defaults: repo_path=".", output_file="CHANGELOG.md"

set -e

REPO_PATH="${1:-.}"
OUTPUT_FILE="${2:-CHANGELOG.md}"

cd "$REPO_PATH"

# Check if git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository: $REPO_PATH"
  exit 1
fi

# Get the last tag (if exists), otherwise start from beginning
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
  echo "Generating changelog since tag: $LAST_TAG"
  COMMITS=$(git log "$LAST_TAG..HEAD" --format="%s" 2>/dev/null || echo "")
else
  echo "No tags found — using last 50 commits"
  COMMITS=$(git log -50 --format="%s" 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
  echo "No commits found."
  exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  # Skip empty lines and merge commits
  [ -z "$line" ] && continue
  [[ "$line" =~ ^Merge ]] && continue

  # Parse conventional commits: type(scope): message
  # Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, BREAKING
  if [[ "$line" =~ ^feat(\(.+\))?: ]]; then
    ADDED="${ADDED}- ${line}\n"
  elif [[ "$line" =~ ^fix(\(.+\))?: ]]; then
    FIXED="${FIXED}- ${line}\n"
  elif [[ "$line" =~ ^refactor!:|breaking[[:space:]] ]]; then
    REMOVED="${REMOVED}- ${line}\n"
  elif [[ "$line" =~ ^(chore|docs|style|perf|ci|build|test)(\(.+\))?: ]]; then
    CHANGED="${CHANGED}- ${line}\n"
  else
    # Default to Changed for unrecognized types
    CHANGED="${CHANGED}- ${line}\n"
  fi
done <<< "$COMMITS"

# Build CHANGELOG content
TAG_DATE=$(date +"%Y-%m-%d")
cat > "$OUTPUT_FILE" << HEADER
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [$TAG_DATE]

HEADER

if [ -n "$ADDED" ]; then
  printf "### Added\n%s\n" "$(echo -e "$ADDED")" >> "$OUTPUT_FILE"
fi

if [ -n "$FIXED" ]; then
  printf "### Fixed\n%s\n" "$(echo -e "$FIXED")" >> "$OUTPUT_FILE"
fi

if [ -n "$CHANGED" ]; then
  printf "### Changed\n%s\n" "$(echo -e "$CHANGED")" >> "$OUTPUT_FILE"
fi

if [ -n "$REMOVED" ]; then
  printf "### Removed\n%s\n" "$(echo -e "$REMOVED")" >> "$OUTPUT_FILE"
fi

echo "✅ CHANGELOG generated: $OUTPUT_FILE"
