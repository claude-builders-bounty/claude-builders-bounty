#!/usr/bin/env bash
set -euo pipefail

# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]

OUTPUT="CHANGELOG.md"
SINCE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

# Find last tag if not specified
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "project")
TODAY=$(date +%Y-%m-%d)

# Collect commits
if [[ -n "$SINCE" ]]; then
  COMMITS=$(git log "${SINCE}..HEAD" --pretty=format:"%s" 2>/dev/null || echo "")
  RANGE="${SINCE}..HEAD"
else
  COMMITS=$(git log --pretty=format:"%s" 2>/dev/null || echo "")
  RANGE="all history"
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found since ${SINCE:-beginning}."
  exit 0
fi

# Categorize commits
ADDED=(); FIXED=(); CHANGED=(); REMOVED=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  msg=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  
  if echo "$msg" | grep -qiE '^(feat|add|new|implement|introduce|create)'; then
    ADDED+=("$msg")
  elif echo "$msg" | grep -qiE '^(fix|bug|patch|resolve|hotfix|correct)'; then
    FIXED+=("$msg")
  elif echo "$msg" | grep -qiE '^(remove|delete|drop|deprecate|retire)'; then
    REMOVED+=("$msg")
  else
    CHANGED+=("$msg")
  fi
done <<< "$COMMITS"

# Generate changelog
{
  echo "# Changelog — ${REPO_NAME}"
  echo ""
  echo "## [Unreleased] — ${TODAY}"
  echo ""
  echo "_Generated from ${RANGE}_"
  echo ""

  section() {
    local title="$1"; shift
    local -a items=("$@")
    if [[ ${#items[@]} -gt 0 ]]; then
      echo "### ${title}"
      for item in "${items[@]}"; do
        echo "- ${item}"
      done
      echo ""
    fi
  }

  section "✨ Added" "${ADDED[@]}"
  section "🐛 Fixed" "${FIXED[@]}"
  section "🔄 Changed" "${CHANGED[@]}"
  section "🗑 Removed" "${REMOVED[@]}"

} > "$OUTPUT"

echo "✅ Changelog written to ${OUTPUT}"
echo "   ${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed"
