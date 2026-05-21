#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh              # since last tag
#   bash changelog.sh v1.2.0       # since specific tag
#   bash changelog.sh --all        # all history
#   bash changelog.sh --dry-run    # preview only
#
# Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1

set -euo pipefail

# --- Parse arguments ---
SINCE_TAG=""
ALL_HISTORY=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --all)       ALL_HISTORY=true ;;
    --dry-run)   DRY_RUN=true ;;
    v*|*)        SINCE_TAG="$arg" ;;
  esac
done

# --- Determine commit range ---
if [ "$ALL_HISTORY" = true ]; then
  COMMIT_RANGE="HEAD"
  RANGE_LABEL="All History"
elif [ -n "$SINCE_TAG" ]; then
  COMMIT_RANGE="$SINCE_TAG..HEAD"
  RANGE_LABEL="$SINCE_TAG...HEAD"
else
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -n "$LAST_TAG" ]; then
    COMMIT_RANGE="$LAST_TAG..HEAD"
    RANGE_LABEL="$LAST_TAG...HEAD"
  else
    COMMIT_RANGE="HEAD"
    RANGE_LABEL="All History (no tags found)"
  fi
fi

# --- Extract version from latest tag or use "Unreleased" ---
if [ "$ALL_HISTORY" = true ] || [ -z "$(git describe --tags --abbrev=0 2>/dev/null || echo '')" ]; then
  VERSION="Unreleased"
else
  VERSION="$(git describe --tags --abbrev=0 2>/dev/null)"
  # Strip leading 'v' if present
  VERSION="${VERSION#v}"
fi

# --- Get today's date ---
TODAY=$(date +%Y-%m-%d)

# --- Categorize commits ---
CATEGORIZE_CMD='
import sys
import re

categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    # Remove leading dash if present
    line = line.lstrip("- ").strip()

    lower = line.lower()

    # Categorize by prefix/keyword
    if any(p in lower for p in ["feat:", "feat(", "add", "new ", "initial", "create", "implement", "introduce"]):
        categories["Added"].append(line)
    elif any(p in lower for p in ["fix:", "fix(", "bug", "patch", "correct", "resolve", "repair", "workaround"]):
        categories["Fixed"].append(line)
    elif any(p in lower for p in ["remove", "delete", "deprecate", "drop", "strip", "eliminate"]):
        categories["Removed"].append(line)
    else:
        categories["Changed"].append(line)

# Print only non-empty categories
order = ["Added", "Fixed", "Changed", "Removed"]
for cat in order:
    items = categories[cat]
    if items:
        print(f"### {cat}")
        for item in items:
            print(f"- {item}")
        print()
'

# --- Get commits and categorize ---
COMMITS=$(git log "$COMMIT_RANGE" --pretty=format:"- %s" --no-merges 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
  echo "No commits found in range: $RANGE_LABEL"
  exit 0
fi

# --- Build changelog content ---
HEADER="# Changelog"
ENTRY_HEADER="## [$VERSION] - $TODAY"
CATEGORIZED=$(echo "$COMMITS" | python3 -c "$CATEGORIZE_CMD")

CHANGELOG_CONTENT="$HEADER

$ENTRY_HEADER

$CATEGORIZED"

# --- Output ---
if [ "$DRY_RUN" = true ]; then
  echo "$CHANGELOG_CONTENT"
else
  # If CHANGELOG.md exists, prepend the new entry
  CHANGELOG_FILE="CHANGELOG.md"
  if [ -f "$CHANGELOG_FILE" ]; then
    # Read existing content (skip the header line)
    EXISTING=$(tail -n +2 "$CHANGELOG_FILE")
    echo "$CHANGELOG_CONTENT" > "$CHANGELOG_FILE"
    echo "$EXISTING" >> "$CHANGELOG_FILE"
  else
    echo "$CHANGELOG_CONTENT" > "$CHANGELOG_FILE"
  fi
  echo "CHANGELOG.md generated successfully!"
  echo "  Range: $RANGE_LABEL"
  echo "  Version: $VERSION"
fi
