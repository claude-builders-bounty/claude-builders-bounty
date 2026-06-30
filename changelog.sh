#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output-file]
# Default output: CHANGELOG.md in current directory

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

cd "$REPO_ROOT"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository. Run 'git init' first." >&2
  exit 1
fi

# Check if there are any commits
if ! git log --oneline -1 > /dev/null 2>&1; then
  echo "Error: No commits found in repository." >&2
  exit 1
fi

echo "# Changelog

All notable changes to this project will be documented in this file.

---

" > "$OUTPUT_FILE"

# Get all tags sorted by version
TAGS=$(git tag --sort=-version:refname 2>/dev/null || git tag --sort=-creatordate 2>/dev/null || "")

if [ -z "$TAGS" ]; then
  # No tags — output all commits
  echo "## Unreleased" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  git log --pretty=format:"- %s (%h)" --reverse >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
else
  # Generate changelog between tags
  PREV_TAG=""
  FIRST_TAG=""

  for TAG in $TAGS; do
    if [ -z "$FIRST_TAG" ]; then
      FIRST_TAG="$TAG"
      continue
    fi

    if [ -n "$PREV_TAG" ]; then
      echo "" >> "$OUTPUT_FILE"
      echo "## [$PREV_TAG] → [$TAG]" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
    else
      echo "" >> "$OUTPUT_FILE"
      echo "## [$TAG]" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
    fi

    # Get commits between tags and categorize
    COMMITS=$(git log --pretty=format:"%s||%h" "$PREV_TAG..$TAG" 2>/dev/null || git log --pretty=format:"%s||%h" -20)

    ADDED=""
    FIXED=""
    CHANGED=""
    REMOVED=""

    while IFS= read -r line; do
      [ -z "$line" ] && continue
      MSG=$(echo "$line" | cut -d'|' -f1)
      HASH=$(echo "$line" | cut -d'|' -f2)

      # Categorize based on conventional commits or keywords
      if echo "$MSG" | grep -qiE "^(feat|add|new|implement|introduce)"; then
        ADDED="${ADDED}- ${MSG} (${HASH})"$'\n'
      elif echo "$MSG" | grep -qiE "^(fix|bug|hotfix|resolve|patch)"; then
        FIXED="${FIXED}- ${MSG} (${HASH})"$'\n'
      elif echo "$MSG" | grep -qiE "^(remove|delete|drop|deprecate)"; then
        REMOVED="${REMOVED}- ${MSG} (${HASH})"$'\n'
      else
        CHANGED="${CHANGED}- ${MSG} (${HASH})"$'\n'
      fi
    done <<< "$COMMITS"

    if [ -n "$ADDED" ]; then
      echo "### Added" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      echo "$ADDED" >> "$OUTPUT_FILE"
    fi

    if [ -n "$FIXED" ]; then
      echo "" >> "$OUTPUT_FILE"
      echo "### Fixed" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      echo "$FIXED" >> "$OUTPUT_FILE"
    fi

    if [ -n "$CHANGED" ]; then
      echo "" >> "$OUTPUT_FILE"
      echo "### Changed" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      echo "$CHANGED" >> "$OUTPUT_FILE"
    fi

    if [ -n "$REMOVED" ]; then
      echo "" >> "$OUTPUT_FILE"
      echo "### Removed" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      echo "$REMOVED" >> "$OUTPUT_FILE"
    fi

    PREV_TAG="$TAG"
  done

  # Add unreleased section for commits after the last tag
  if [ -n "$FIRST_TAG" ]; then
    UNRELEASED_COMMITS=$(git log --pretty=format:"%s||%h" "$FIRST_TAG..HEAD" 2>/dev/null || "")
    if [ -n "$UNRELEASED_COMMITS" ]; then
      echo "" >> "$OUTPUT_FILE"
      echo "## [Unreleased]" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      echo "### Uncommitted changes since $FIRST_TAG" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      while IFS= read -r line; do
        [ -z "$line" ] && continue
        MSG=$(echo "$line" | cut -d'|' -f1)
        HASH=$(echo "$line" | cut -d'|' -f2)
        echo "- ${MSG} (${HASH})" >> "$OUTPUT_FILE"
      done <<< "$UNRELEASED_COMMITS"
    fi
  fi
fi

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "Generated on $(date -u '+%Y-%m-%d %H:%M:%S UTC') using [changelog.sh](changelog.sh)" >> "$OUTPUT_FILE"

echo "✅ CHANGELOG generated: $OUTPUT_FILE"
