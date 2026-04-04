#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Auto-generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>] [--version <v>]
# =============================================================================

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
DATE=$(date +"%Y-%m-%d")
VERSION="Unreleased"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)   SINCE_TAG="$2"; shift 2 ;;
    --output)  OUTPUT_FILE="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --help)
      echo "Usage: bash changelog.sh [--since <tag>] [--output <file>] [--version <v>]"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "❌  Not inside a git repository."
  exit 1
fi

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -z "$SINCE_TAG" ]]; then
  echo "ℹ️  No git tags found — scanning full history."
  RANGE_LABEL="beginning of history"
  COMMITS=$(git log --pretty=format:"%s" --no-merges 2>/dev/null || true)
else
  echo "ℹ️  Generating changelog since tag: $SINCE_TAG"
  RANGE_LABEL="$SINCE_TAG"
  COMMITS=$(git log "${SINCE_TAG}..HEAD" --pretty=format:"%s" --no-merges 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "⚠️  No commits found since $RANGE_LABEL."
  exit 0
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

categorize() {
  local subject="$1"
  # Strip conventional-commit prefix for display
  local clean
  clean=$(echo "$subject" | sed -E 's/^[a-z]+(\([^)]*\))?!?:\s*//')
  local lower
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(feat|add|new|create|introduce|implement)(\(|:|[[:space:]])'; then
    ADDED+=("$clean")
  elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|hotfix|correct|revert)(\(|:|[[:space:]])'; then
    FIXED+=("$clean")
  elif echo "$lower" | grep -qE '^(remove|delete|del|drop|deprecate)(\(|:|[[:space:]])'; then
    REMOVED+=("$clean")
  elif echo "$lower" | grep -qE '^(refactor|update|change|improve|upgrade|bump|style|perf|chore|build|ci|docs|test)(\(|:|[[:space:]])'; then
    CHANGED+=("$clean")
  elif echo "$lower" | grep -qE '[[:space:]](add|added|adds|new|creat|introduc|implement)[[:space:]]|^(add|creat|new[[:space:]])'; then
    ADDED+=("$clean")
  elif echo "$lower" | grep -qE '[[:space:]](fix|fixed|bug|patch|resolv|hotfix)[[:space:]]|^fix[[:space:]]'; then
    FIXED+=("$clean")
  elif echo "$lower" | grep -qE '[[:space:]](remov|delet|drop|deprecat)[[:space:]]'; then
    REMOVED+=("$clean")
  elif echo "$lower" | grep -qE '[[:space:]](updat|chang|refactor|improv|upgrad|bump|migrat|renam)[[:space:]]'; then
    CHANGED+=("$clean")
  else
    OTHER+=("$clean")
  fi
}

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  categorize "$subject"
done <<< "$COMMITS"

# Preserve existing previous-version sections
EXISTING=""
if [[ -f "$OUTPUT_FILE" ]]; then
  EXISTING=$(awk '/^## \[/{found++} found>=1{print}' "$OUTPUT_FILE" 2>/dev/null || true)
fi

{
  cat <<HEADER
# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [$VERSION] — $DATE
*(changes since ${RANGE_LABEL})*
HEADER

  write_section() {
    local title="$1"; shift
    echo ""
    echo "### $title"
    for item in "$@"; do
      echo "- $item"
    done
  }

  [[ ${#ADDED[@]}   -gt 0 ]] && write_section "Added"   "${ADDED[@]}"
  [[ ${#FIXED[@]}   -gt 0 ]] && write_section "Fixed"   "${FIXED[@]}"
  [[ ${#CHANGED[@]} -gt 0 ]] && write_section "Changed" "${CHANGED[@]}"
  [[ ${#REMOVED[@]} -gt 0 ]] && write_section "Removed" "${REMOVED[@]}"
  [[ ${#OTHER[@]}   -gt 0 ]] && write_section "Other"   "${OTHER[@]}"

  echo ""

  if [[ -n "$EXISTING" ]]; then
    echo "---"
    echo ""
    echo "$EXISTING"
  fi
} > "$OUTPUT_FILE"

echo ""
echo "✅  CHANGELOG written to: $OUTPUT_FILE"
echo "   ✨ Added   : ${#ADDED[@]}"
echo "   🐛 Fixed   : ${#FIXED[@]}"
echo "   🔧 Changed : ${#CHANGED[@]}"
echo "   🗑️  Removed : ${#REMOVED[@]}"
[[ ${#OTHER[@]} -gt 0 ]] && echo "   📝 Other   : ${#OTHER[@]}"