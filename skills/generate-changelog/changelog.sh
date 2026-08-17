#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <ref>] [--output CHANGELOG.md]
set -euo pipefail

SINCE_REF="${1:-}"
OUTPUT_FILE="CHANGELOG.md"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE_REF="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    *) SINCE_REF="$1"; shift ;;
  esac
done

# Determine the range: commits since the last git tag
if [[ -z "$SINCE_REF" ]]; then
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$LAST_TAG" ]]; then
    SINCE_REF="$LAST_TAG"
  else
    SINCE_REF="$(git rev-list --max-parents=0 HEAD 2>/dev/null | tail -1)"
  fi
fi

if [[ -z "$SINCE_REF" ]]; then
  echo "ERROR: no git history found" >&2
  exit 1
fi

# Categorize commits by conventional-commit prefix
categorize() {
  local msg="$1"
  local lower
  lower="$(echo "$msg" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower" =~ ^(fix|bugfix|hotfix|bug)(\(.*\))?!?: ]]; then
    echo "Fixed"
  elif [[ "$lower" =~ ^(feat|feature|add|new)(\(.*\))?!?: ]]; then
    echo "Added"
  elif [[ "$lower" =~ ^(refactor|perf|performance|style|chore|build|ci|docs|test)(\(.*\))?!?: ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^(remove|delete|deprecate)(\(.*\))?!?: ]]; then
    echo "Removed"
  else
    echo "Changed"
  fi
}

# Build categorized sections
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  msg="${line#*|}"   # format: HASH|SUBJECT
  hash="${line%%|*}"
  cat="$(categorize "$msg")"
  short_hash="${hash:0:7}"
  case "$cat" in
    Added)   ADDED+="  - ${msg} (\`${short_hash}\`)\n" ;;
    Fixed)   FIXED+="  - ${msg} (\`${short_hash}\`)\n" ;;
    Removed) REMOVED+="  - ${msg} (\`${short_hash}\`)\n" ;;
    Changed) CHANGED+="  - ${msg} (\`${short_hash}\`)\n" ;;
  esac
done < <(git log --no-merges --format="%h|%s" "${SINCE_REF}..HEAD" 2>/dev/null || git log --no-merges --format="%h|%s" "${SINCE_REF}" 2>/dev/null)

# Write output
{
  echo "# Changelog"
  echo ""
  echo "Generated from \`git log\` since \`${SINCE_REF}\` on $(date +%Y-%m-%d)."
  echo ""
  echo "## Added"
  echo -e "${ADDED:-  - none}"
  echo "## Fixed"
  echo -e "${FIXED:-  - none}"
  echo "## Changed"
  echo -e "${CHANGED:-  - none}"
  echo "## Removed"
  echo -e "${REMOVED:-  - none}"
} > "$OUTPUT_FILE"

echo "✅ CHANGELOG.md written (since ${SINCE_REF})"
