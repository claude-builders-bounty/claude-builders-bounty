#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output CHANGELOG.md]
# Works with any git repo. Auto-categorizes commits by conventional commit prefix.

set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Get the last tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Get current date and latest tag/version
CURRENT_DATE=$(date +%Y-%m-%d)
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD")

# Fetch commits since last tag (or all commits if no tag)
if [[ -n "$SINCE_TAG" ]]; then
  COMMITS=$(git log "${SINCE_TAG}..HEAD" --pretty=format:"%H %s" 2>/dev/null)
else
  COMMITS=$(git log --pretty=format:"%H %s" 2>/dev/null)
fi

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

# Categorize commits by conventional commit prefix
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  hash="${line%% *}"
  msg="${line#* }"
  short_hash="${hash:0:7}"

  if [[ "$msg" =~ ^feat(\(.+\))?!?:\ (.+) ]]; then
    ADDED+=("- ${BASH_REMATCH[2]} (\`$short_hash\`)")
  elif [[ "$msg" =~ ^fix(\(.+\))?!?:\ (.+) ]]; then
    FIXED+=("- ${BASH_REMATCH[2]} (\`$short_hash\`)")
  elif [[ "$msg" =~ ^(refactor|perf|style|build|ci|docs|chore)(\(.+\))?!?:\ (.+) ]]; then
    CHANGED+=("- ${BASH_REMATCH[3]} (\`$short_hash\`)")
  elif [[ "$msg" =~ ^(remove|delete|drop)(\(.+\))?!?:\ (.+) ]]; then
    REMOVED+=("- ${BASH_REMATCH[3]} (\`$short_hash\`)")
  elif [[ "$msg" =~ ^revert ]]; then
    REMOVED+=("- $msg (\`$short_hash\`)")
  else
    # Non-conventional commits go into Changed
    CHANGED+=("- $msg (\`$short_hash\`)")
  fi
done <<< "$COMMITS"

# Build the CHANGELOG content
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "## [Unreleased] — $CURRENT_DATE"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    for item in "${ADDED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    for item in "${FIXED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    for item in "${CHANGED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    for item in "${REMOVED[@]}"; do echo "$item"; done
    echo ""
  fi

  # Append any existing CHANGELOG content below
  if [[ -f "$OUTPUT" ]]; then
    echo "---"
    echo ""
    tail -n +3 "$OUTPUT"
  fi
} > "${OUTPUT}.tmp"

mv "${OUTPUT}.tmp" "$OUTPUT"
echo "✅ CHANGELOG written to $OUTPUT"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]}"
