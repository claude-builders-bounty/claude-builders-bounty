#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh                  # generate since latest tag
#   bash changelog.sh --since TAG      # generate since a specific tag
#   bash changelog.sh --output FILE    # change output file (default: CHANGELOG.md)
#   bash changelog.sh --repo-path PATH # path to git repo (default: current dir)
#
# Commits are auto-categorized by conventional commit prefixes:
#   feat:/add:  → Added
#   fix:/bug:   → Fixed
#   change:/refactor: → Changed
#   remove:/drop: → Removed

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
REPO_PATH="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)
      SINCE_TAG="$2"; shift 2 ;;
    --output)
      OUTPUT_FILE="$2"; shift 2 ;;
    --repo-path)
      REPO_PATH="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--since TAG] [--output FILE] [--repo-path PATH]"
      exit 0 ;;
    *)
      echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -d "$REPO_PATH/.git" ]]; then
  echo "Error: $REPO_PATH is not a git repository" >&2
  exit 1
fi

# Auto-detect the latest tag if --since not provided
if [[ -z "$SINCE_TAG" ]]; then
  LATEST_TAG=$(git -C "$REPO_PATH" describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    SINCE_TAG="$LATEST_TAG"
  fi
fi

# Build git log command
GIT_CMD=(git -C "$REPO_PATH" log --pretty=format:"%h %s" --no-merges)
if [[ -n "$SINCE_TAG" ]]; then
  GIT_CMD+=("$SINCE_TAG..HEAD")
fi

# Categorize commits
declare -A ENTRIES
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  hash="${line%% *}"
  msg="${line#* }"
  case "$msg" in
    feat:*|add:*|Add:*|Added:*) CAT="Added" ;;
    fix:*|bug:*|Fix:*|Fixed:*) CAT="Fixed" ;;
    change:*|chore:*|refactor:*|Change:*|Changed:*) CAT="Changed" ;;
    remove:*|drop:*|Remove:*|Removed:*) CAT="Removed" ;;
    *) CAT="Other" ;;
  esac
  ENTRIES["$CAT"]+="- ${msg} (${hash})"$'\n'
done < <("${GIT_CMD[@]}" 2>/dev/null || true)

# Write CHANGELOG.md
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  if [[ -n "$SINCE_TAG" ]]; then
    echo "> Generated since tag: \`${SINCE_TAG}\`"
    echo ""
  fi
  for CAT in Added Fixed Changed Removed Other; do
    if [[ -n "${ENTRIES[$CAT]:-}" ]]; then
      echo "## ${CAT}"
      echo ""
      printf '%s' "${ENTRIES[$CAT]}"
      echo ""
    fi
  done
} > "$OUTPUT_FILE"

echo "CHANGELOG generated at $OUTPUT_FILE"