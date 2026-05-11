#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage: bash changelog.sh [--since <tag|commit>] [--output <file>]
#
# If --since is omitted, uses the most recent git tag.
# If no tags exist, includes the entire history.

set -euo pipefail

# --- Defaults ---
SINCE=""
OUTPUT="CHANGELOG.md"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--since <tag|commit>] [--output <file>]"
      echo "  --since   Start point (tag or commit). Default: latest tag or root."
      echo "  --output  Output file. Default: CHANGELOG.md"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Determine the range ---
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
  SINCE_LABEL="since \`${SINCE}\`"
else
  RANGE=""
  SINCE_LABEL="(full history)"
fi

# --- Get the new version label ---
NEW_VERSION=$(git describe --tags --always 2>/dev/null || echo "Unreleased")
TODAY=$(date '+%Y-%m-%d')

# --- Collect commits ---
if [[ -n "$RANGE" ]]; then
  COMMITS=$(git log "$RANGE" --pretty=format:"%s" --no-merges 2>/dev/null || echo "")
else
  COMMITS=$(git log --pretty=format:"%s" --no-merges 2>/dev/null || echo "")
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found ${SINCE_LABEL}. Nothing to generate."
  exit 0
fi

# --- Categorize commits ---
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r msg; do
  # Normalize: lowercase for matching, original for display
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  # Strip conventional commit prefix for display
  display=$(echo "$msg" | sed -E 's/^(feat|fix|refactor|docs|test|chore|perf|ci|style|build|revert)(\([^)]*\))?:\s*//')

  case "$lower" in
    feat:*|feat\(*|add:*|add\ *|added\ *|new:*|new\ *|implement*)
      ADDED="${ADDED}\n- ${display}"
      ;;
    fix:*|fix\(*|fixed\ *|bugfix*|hotfix*|patch:*|resolve*)
      FIXED="${FIXED}\n- ${display}"
      ;;
    remove:*|remove\ *|removed\ *|delete:*|delete\ *|deprecated*|deprecate:*)
      REMOVED="${REMOVED}\n- ${display}"
      ;;
    refactor:*|refactor\(*|update:*|update\ *|updated\ *|change:*|changed\ *|improve*|enhance*|perf:*|perf\(*|chore:*|chore\(*|ci:*|ci\(*|build:*|build\(*|style:*|style\(*|docs:*|docs\(*)
      CHANGED="${CHANGED}\n- ${display}"
      ;;
    revert:*|revert\ *)
      REMOVED="${REMOVED}\n- ${display}"
      ;;
    *)
      OTHER="${OTHER}\n- ${msg}"
      ;;
  esac
done <<< "$COMMITS"

# --- Build the changelog ---
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to **${REPO_NAME}** are documented in this file."
  echo ""
  echo "## [${NEW_VERSION}] — ${TODAY}"
  echo ""

  if [[ -n "$ADDED" ]]; then
    echo "### Added"
    echo -e "$ADDED"
    echo ""
  fi

  if [[ -n "$FIXED" ]]; then
    echo "### Fixed"
    echo -e "$FIXED"
    echo ""
  fi

  if [[ -n "$CHANGED" ]]; then
    echo "### Changed"
    echo -e "$CHANGED"
    echo ""
  fi

  if [[ -n "$REMOVED" ]]; then
    echo "### Removed"
    echo -e "$REMOVED"
    echo ""
  fi

  if [[ -n "$OTHER" ]]; then
    echo "### Other"
    echo -e "$OTHER"
    echo ""
  fi

  echo "---"
  echo "*Generated ${SINCE_LABEL} on ${TODAY} by [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty)*"
} > "$OUTPUT"

echo "✅ ${OUTPUT} generated (${SINCE_LABEL}, $(echo "$COMMITS" | wc -l | tr -d ' ') commits categorized)"
