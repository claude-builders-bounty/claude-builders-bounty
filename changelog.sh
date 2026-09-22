#!/usr/bin/env bash
# ==============================================================================
# Script: changelog.sh
# Purpose: Automatically generate a structured CHANGELOG.md from git history
# Features:
#   - Detects the latest git tag (or falls back to the initial commit)
#   - Auto-categorizes commits into: Added, Fixed, Changed, Removed
#   - Supports Conventional Commits (feat, fix, refactor, etc.) and semantic keywords
#   - Formats clean Markdown following 'Keep a Changelog' standards
# ==============================================================================

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
DRY_RUN=false
TARGET_TAG=""

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -t|--tag)
      TARGET_TAG="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      echo "Usage: bash changelog.sh [options]"
      echo ""
      echo "Options:"
      echo "  -o, --output <file>  Specify output file (default: CHANGELOG.md)"
      echo "  -t, --tag <tag>      Specify base git tag to compare from"
      echo "  --dry-run            Print changelog to stdout without writing to file"
      echo "  -h, --help           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Ensure we are inside a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Must be run inside a valid git repository." >&2
  exit 1
fi

# Detect base tag or initial commit
if [[ -z "$TARGET_TAG" ]]; then
  if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    TARGET_TAG=$(git describe --tags --abbrev=0)
    COMMIT_RANGE="${TARGET_TAG}..HEAD"
    TAG_LABEL="since tag: $TARGET_TAG"
  else
    # No tags found, get all commits from beginning
    COMMIT_RANGE="HEAD"
    TAG_LABEL="initial release (all commits)"
  fi
else
  COMMIT_RANGE="${TARGET_TAG}..HEAD"
  TAG_LABEL="since tag: $TARGET_TAG"
fi

TODAY=$(date +'%Y-%m-%d')

# Arrays for categorized changes
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Read commits into arrays
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" ]] && continue

  HASH=$(echo "$line" | cut -d' ' -f1)
  MSG=$(echo "$line" | cut -d' ' -f2-)
  LOWER_MSG=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')

  ENTRY="- ${MSG} (\`${HASH}\`)"

  # Categorization logic
  if [[ "$LOWER_MSG" =~ ^(feat|feature|add)(\([a-z0-9_-]+\))?: ]] || [[ "$LOWER_MSG" =~ ^(add|added|create|implement|support|introducing) ]]; then
    ADDED+=("$ENTRY")
  elif [[ "$LOWER_MSG" =~ ^(fix|bug|hotfix|patch)(\([a-z0-9_-]+\))?: ]] || [[ "$LOWER_MSG" =~ ^(fix|fixed|resolve|resolving|bugfix|patch) ]]; then
    FIXED+=("$ENTRY")
  elif [[ "$LOWER_MSG" =~ ^(remove|delete|drop|deprecate)(\([a-z0-9_-]+\))?: ]] || [[ "$LOWER_MSG" =~ ^(remove|removed|delete|deleted|deprecated) ]]; then
    REMOVED+=("$ENTRY")
  else
    # Default to Changed (includes refactor, perf, chore, docs, style, update)
    CHANGED+=("$ENTRY")
  fi
done < <(git log "$COMMIT_RANGE" --pretty=format:"%h %s" 2>/dev/null || true)

# Build the Markdown content
BUILD_BUFFER=""
BUILD_BUFFER+="# Changelog\n\n"
BUILD_BUFFER+="All notable changes to this project will be documented in this file.\n"
BUILD_BUFFER+="The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n"
BUILD_BUFFER+="## [Unreleased] - ${TODAY} (${TAG_LABEL})\n\n"

HAS_ENTRIES=false

if [[ ${#ADDED[@]} -gt 0 ]]; then
  HAS_ENTRIES=true
  BUILD_BUFFER+="### Added\n"
  for item in "${ADDED[@]}"; do
    BUILD_BUFFER+="${item}\n"
  done
  BUILD_BUFFER+="\n"
fi

if [[ ${#FIXED[@]} -gt 0 ]]; then
  HAS_ENTRIES=true
  BUILD_BUFFER+="### Fixed\n"
  for item in "${FIXED[@]}"; do
    BUILD_BUFFER+="${item}\n"
  done
  BUILD_BUFFER+="\n"
fi

if [[ ${#CHANGED[@]} -gt 0 ]]; then
  HAS_ENTRIES=true
  BUILD_BUFFER+="### Changed\n"
  for item in "${CHANGED[@]}"; do
    BUILD_BUFFER+="${item}\n"
  done
  BUILD_BUFFER+="\n"
fi

if [[ ${#REMOVED[@]} -gt 0 ]]; then
  HAS_ENTRIES=true
  BUILD_BUFFER+="### Removed\n"
  for item in "${REMOVED[@]}"; do
    BUILD_BUFFER+="${item}\n"
  done
  BUILD_BUFFER+="\n"
fi

if [[ "$HAS_ENTRIES" = false ]]; then
  BUILD_BUFFER+="*No new commits found in range: ${COMMIT_RANGE}*\n\n"
fi

# Output handling
if [[ "$DRY_RUN" = true ]]; then
  echo -e "$BUILD_BUFFER"
else
  echo -e "$BUILD_BUFFER" > "$OUTPUT_FILE"
  echo "✅ Successfully generated changelog in '$OUTPUT_FILE' ($TAG_LABEL)."
fi
