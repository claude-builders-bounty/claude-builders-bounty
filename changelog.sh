#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [version]
set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  # default version = today's date, or next tag if tags exist
  VERSION="$(date +%Y-%m-%d)"
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

echo "## [$VERSION] - $(date +%Y-%m-%d)"
echo ""

if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  echo "_(changes since $LAST_TAG)_"
else
  RANGE="HEAD"
  echo "_(initial release)_"
fi
echo ""

# Collect + categorize commits
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""

while IFS= read -r line; do
  # strip the short hash, keep the message
  msg="$(echo "$line" | sed 's/^[a-f0-9]\{7,12\} //')"
  case "$msg" in
    feat*|add*|Add*|feature*)  ADDED="$ADDED- $msg\n" ;;
    fix*|bug*|Fix*)            FIXED="$FIXED- $msg\n" ;;
    remove*|drop*|delete*|Remove*) REMOVED="$REMOVED- $msg\n" ;;
    *)                         CHANGED="$CHANGED- $msg\n" ;;
  esac
done < <(git log "$RANGE" --pretty=format:'%h %s' 2>/dev/null)

emit() {
  local title="$1" body="$2"
  if [ -n "$body" ]; then
    echo "### $title"
    echo -e "$body"
    echo ""
  fi
}

emit "Added"   "$ADDED"
emit "Fixed"   "$FIXED"
emit "Changed" "$CHANGED"
emit "Removed" "$REMOVED"
