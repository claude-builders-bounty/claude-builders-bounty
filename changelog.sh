#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh                     → writes to CHANGELOG.md
#   bash changelog.sh --stdout            → prints to stdout
#   bash changelog.sh --tag v1.0.0        → start from a specific tag
#   bash changelog.sh --repo /path/to/repo → use another repo
# =============================================================================

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
WRITE_MODE="file"
START_TAG=""
TARGET_DIR="."

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout) WRITE_MODE="stdout"; shift ;;
    --tag)    START_TAG="$2";  shift 2 ;;
    --repo)   TARGET_DIR="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: bash changelog.sh [--stdout] [--tag <tag>] [--repo <path>]"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Validate repo
cd "$TARGET_DIR"
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: $TARGET_DIR is not a git repository."
  echo "Run this script from within a git repo or use --repo <path>."
  exit 1
fi

REPO_NAME=$(basename "$(git rev-parse --show-toplevel)" 2>/dev/null || echo "unknown")

# Determine tag range
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -z "$LATEST_TAG" && -z "$START_TAG" ]]; then
  # No tags at all — use all commits
  TAG_RANGE=""
  TAG_LABEL="initial"
elif [[ -n "$START_TAG" ]]; then
  TAG_RANGE="${START_TAG}..HEAD"
  TAG_LABEL="$START_TAG"
else
  TAG_RANGE="${LATEST_TAG}..HEAD"
  TAG_LABEL="$LATEST_TAG"
fi

# Gather commits
if [[ -z "${TAG_RANGE:-}" ]]; then
  COMMITS=$(git log --pretty=format:"%H|%s" 2>/dev/null)
else
  COMMITS=$(git log "$TAG_RANGE" --pretty=format:"%H|%s" 2>/dev/null)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No new commits found since last tag (${TAG_LABEL:-none})."
  exit 0
fi

# Categorize commits
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS='|' read -r HASH MESSAGE; do
  MSG_LC=$(echo "$MESSAGE" | tr '[:upper:]' '[:lower:]')
  SHORT_HASH="${HASH:0:7}"

  if echo "$MSG_LC" | grep -qE '^(feat|add|feature|implement|create|new):? '; then
    ADDED+=("$SHORT_HASH|$MESSAGE")
  elif echo "$MSG_LC" | grep -qE '^(fix|bug|hotfix|patch|correct|resolve):? '; then
    FIXED+=("$SHORT_HASH|$MESSAGE")
  elif echo "$MSG_LC" | grep -qE '^(change|update|refactor|improve|migrate|bump|upgrade|perf|optimize):? '; then
    CHANGED+=("$SHORT_HASH|$MESSAGE")
  elif echo "$MSG_LC" | grep -qE '^(remove|delete|drop|deprecate|cleanup):? '; then
    REMOVED+=("$SHORT_HASH|$MESSAGE")
  elif echo "$MSG_LC" | grep -qE '^(chore|docs|test|ci|style|build|revert|merge):? '; then
    OTHER+=("$SHORT_HASH|$MESSAGE")
  else
    # Try conventional commit detection by prefix
    if echo "$MSG_LC" | grep -qE '^feat(\(.*\))?!?:'; then
      ADDED+=("$SHORT_HASH|$MESSAGE")
    elif echo "$MSG_LC" | grep -qE '^fix(\(.*\))?!?:'; then
      FIXED+=("$SHORT_HASH|$MESSAGE")
    elif echo "$MSG_LC" | grep -qE '^(chore|docs|test|ci|style|build|refactor|perf)(\(.*\))?!?:'; then
      OTHER+=("$SHORT_HASH|$MESSAGE")
    else
      OTHER+=("$SHORT_HASH|$MESSAGE")
    fi
  fi
done <<< "$COMMITS"

# Build CHANGELOG content
NOW=$(date +"%Y-%m-%d")
CONTENT="# Changelog\n\n"
CONTENT+="## [Unreleased] — ${NOW}\n\n"
CONTENT+="> Auto-generated from git history.\n\n"

CONTENT+="### Added\n"
if [[ ${#ADDED[@]} -eq 0 ]]; then CONTENT+="- None\n"; fi
for item in "${ADDED[@]}"; do
  HASH="${item%%|*}"
  MSG="${item#*|}"
  CONTENT+="- ${MSG} (\`${HASH}\`)\n"
done
CONTENT+="\n"

CONTENT+="### Fixed\n"
if [[ ${#FIXED[@]} -eq 0 ]]; then CONTENT+="- None\n"; fi
for item in "${FIXED[@]}"; do
  HASH="${item%%|*}"
  MSG="${item#*|}"
  CONTENT+="- ${MSG} (\`${HASH}\`)\n"
done
CONTENT+="\n"

CONTENT+="### Changed\n"
if [[ ${#CHANGED[@]} -eq 0 ]]; then CONTENT+="- None\n"; fi
for item in "${CHANGED[@]}"; do
  HASH="${item%%|*}"
  MSG="${item#*|}"
  CONTENT+="- ${MSG} (\`${HASH}\`)\n"
done
CONTENT+="\n"

CONTENT+="### Removed\n"
if [[ ${#REMOVED[@]} -eq 0 ]]; then CONTENT+="- None\n"; fi
for item in "${REMOVED[@]}"; do
  HASH="${item%%|*}"
  MSG="${item#*|}"
  CONTENT+="- ${MSG} (\`${HASH}\`)\n"
done
CONTENT+="\n"

# Include other categories as a bonus
if [[ ${#OTHER[@]} -gt 0 ]]; then
  CONTENT+="### Other\n"
  for item in "${OTHER[@]}"; do
    HASH="${item%%|*}"
    MSG="${item#*|}"
    CONTENT+="- ${MSG} (\`${HASH}\`)\n"
  done
  CONTENT+="\n"
fi

# Count stats
TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]}))
CONTENT+="---\n"
CONTENT+="_${TOTAL} commits · $(date +'%B %d, %Y')_\n"

# Output
if [[ "$WRITE_MODE" == "stdout" ]]; then
  echo -e "$CONTENT"
else
  echo -e "$CONTENT" > "$OUTPUT_FILE"
  echo "✅ CHANGELOG.md generated with ${TOTAL} commits across $( \
    ([[ ${#ADDED[@]} -gt 0 ]] && echo -n "Added:${#ADDED[@]} ") || true; \
    ([[ ${#FIXED[@]} -gt 0 ]] && echo -n "Fixed:${#FIXED[@]} ") || true; \
    ([[ ${#CHANGED[@]} -gt 0 ]] && echo -n "Changed:${#CHANGED[@]} ") || true; \
    ([[ ${#REMOVED[@]} -gt 0 ]] && echo -n "Removed:${#REMOVED[@]} ") || true; \
  )categories."
fi
