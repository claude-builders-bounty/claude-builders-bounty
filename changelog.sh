#!/bin/bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--repo PATH] [--output FILE] [--since TAG]

set -euo pipefail

REPO="${PWD}"
OUTPUT="CHANGELOG.md"
SINCE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --since) SINCE="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: bash changelog.sh [--repo PATH] [--output FILE] [--since TAG]"
      echo "  --repo PATH    Path to git repository (default: current dir)"
      echo "  --output FILE  Output file (default: CHANGELOG.md)"
      echo "  --since TAG    Starting tag/ref (default: latest tag)"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

cd "$REPO"

# Get the latest tag as starting point
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -z "$SINCE" ]]; then
  COMMITS=$(git log --pretty=format:"%H|%s|%an|%ad" --date=short --no-merges 2>/dev/null || true)
  VERSION="0.1.0"
else
  COMMITS=$(git log "${SINCE}..HEAD" --pretty=format:"%H|%s|%an|%ad" --date=short --no-merges 2>/dev/null || true)
  VERSION="$SINCE"
fi

DATE=$(date +%Y-%m-%d)

if [[ -z "$COMMITS" ]]; then
  echo "No new commits found since ${SINCE:-the beginning}."
  exit 0
fi

# Categorize commits
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; DEPRECATED=""; SECURITY=""; OTHER=""

while IFS='|' read -r hash msg author date; do
  msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  CATEGORY="OTHER"
  if echo "$msg_lower" | grep -qE '^(feat|feature|add|new|implement|create)'; then
    CATEGORY="ADDED"
  elif echo "$msg_lower" | grep -qE '^(fix|bugfix|hotfix|patch|correct|repair)'; then
    CATEGORY="FIXED"
  elif echo "$msg_lower" | grep -qE '^(change|update|refactor|modify|improve|optimize|redesign|migrate|upgrade)'; then
    CATEGORY="CHANGED"
  elif echo "$msg_lower" | grep -qE '^(remove|delete|deprecate|drop|cleanup)'; then
    CATEGORY="REMOVED"
  elif echo "$msg_lower" | grep -qE '^(deprecat)'; then
    CATEGORY="DEPRECATED"
  elif echo "$msg_lower" | grep -qE '^(sec|security|vuln|vulnerability)'; then
    CATEGORY="SECURITY"
  fi

  clean_msg=$(echo "$msg" | sed -E 's/^(feat|fix|chore|refactor|docs|style|test|perf|ci|build|revert)(\([^)]*\))?[!]?:\s*//i' | sed -E 's/^[A-Z][a-z]+:\s*//')
  SHORT=${hash:0:7}
  ENTRY="  - ${clean_msg} ([${SHORT}](https://github.com/placeholder/placeholder/commit/${hash}))"

  case "$CATEGORY" in
    ADDED) ADDED+="${ENTRY}"$'\n' ;;
    FIXED) FIXED+="${ENTRY}"$'\n' ;;
    CHANGED) CHANGED+="${ENTRY}"$'\n' ;;
    REMOVED) REMOVED+="${ENTRY}"$'\n' ;;
    DEPRECATED) DEPRECATED+="${ENTRY}"$'\n' ;;
    SECURITY) SECURITY+="${ENTRY}"$'\n' ;;
    *) OTHER+="${ENTRY}"$'\n' ;;
  esac
done <<< "$COMMITS"

# Write CHANGELOG
{
  echo "# Changelog"
  echo ""
  echo "## [${VERSION}] - ${DATE}"
  echo ""

  write_section() {
    local name="$1" content="$2"
    if [[ -n "$content" ]]; then
      echo "### $name"
      echo ""
      echo "$content"
    fi
  }

  write_section "Added" "$ADDED"
  write_section "Fixed" "$FIXED"
  write_section "Changed" "$CHANGED"
  write_section "Removed" "$REMOVED"
  write_section "Deprecated" "$DEPRECATED"
  write_section "Security" "$SECURITY"
  write_section "Uncategorized" "$OTHER"
} > "$OUTPUT"

echo "Generated: $(pwd)/${OUTPUT}"
echo "Commits: $(echo "$COMMITS" | wc -l)"
