#!/usr/bin/env bash
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE=""

usage() {
  cat <<'EOF'
Usage: changelog.sh [--output CHANGELOG.md] [--since <tag>]

Generate a structured CHANGELOG.md from git history since the last tag.
Commits are auto-categorized by Conventional Commits prefixes.

Options:
  --output <path>   Output file path (default: CHANGELOG.md)
  --since <tag>     Start from a specific tag instead of the latest
  --help            Show this message
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --since)  SINCE="$2"; shift 2 ;;
    --help)   usage ;;
    *) shift ;;
  esac
done

if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
else
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    RANGE="${LATEST_TAG}..HEAD"
  else
    RANGE="HEAD"
  fi
fi

COMMITS=$(git log "$RANGE" --no-merges --pretty=format:'%s' 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range: $RANGE"
  exit 0
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  msg_lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')

  if echo "$msg_lower" | grep -qE '^(feat|add|create|implement|introduce|new)[(: ]'; then
    ADDED+="- ${line}"$'\n'
  elif echo "$msg_lower" | grep -qE '^(fix|bug|hotfix|patch|resolve|correct|repair)[(: ]'; then
    FIXED+="- ${line}"$'\n'
  elif echo "$msg_lower" | grep -qE '^(revert|remove|drop|delete|deprecate)[(: ]'; then
    REMOVED+="- ${line}"$'\n'
  else
    CHANGED+="- ${line}"$'\n'
  fi
done <<< "$COMMITS"

if [[ -n "${SINCE:-}" ]]; then
  VERSION="${SINCE} -> HEAD"
elif [[ -n "${LATEST_TAG:-}" ]]; then
  VERSION="${LATEST_TAG} -> HEAD"
else
  VERSION="Unreleased"
fi

{
  echo "# Changelog"
  echo ""
  echo "## ${VERSION}"
  echo ""
  if [[ -n "$ADDED" ]]; then
    echo "### Added"
    echo "$ADDED"
  fi
  if [[ -n "$FIXED" ]]; then
    echo "### Fixed"
    echo "$FIXED"
  fi
  if [[ -n "$CHANGED" ]]; then
    echo "### Changed"
    echo "$CHANGED"
  fi
  if [[ -n "$REMOVED" ]]; then
    echo "### Removed"
    echo "$REMOVED"
  fi
  echo ""
  echo "---"
  echo "*Generated on $(date '+%Y-%m-%d %H:%M')*"
} > "$OUTPUT"

echo "Changelog written to $OUTPUT ($(echo "$COMMITS" | wc -l) commits)"
