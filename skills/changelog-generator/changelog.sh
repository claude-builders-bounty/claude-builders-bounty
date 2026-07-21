#!/usr/bin/env bash
set -euo pipefail

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

OUTPUT="CHANGELOG.md"

get_commits() {
  if [ -n "$LAST_TAG" ]; then
    git log "$LAST_TAG..HEAD" --oneline --no-decorate 2>/dev/null || git log --oneline --no-decorate
  else
    git log --oneline --no-decorate
  fi
}

CAT_ADDED=""
CAT_FIXED=""
CAT_CHANGED=""
CAT_REMOVED=""

while IFS= read -r line; do
  hash=$(echo "$line" | cut -d' ' -f1)
  msg=$(echo "$line" | cut -d' ' -f2-)
  lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$lower_msg" | grep -qE '^(feat|add|feature|implement|create|new):?'; then
    CAT_ADDED="$CAT_ADDED  - $msg ($hash)\n"
  elif echo "$lower_msg" | grep -qE '^(fix|bugfix|patch|hotfix|correct|resolve):?'; then
    CAT_FIXED="$CAT_FIXED  - $msg ($hash)\n"
  elif echo "$lower_msg" | grep -qE '^(remove|delete|deprecate|drop|clean):?'; then
    CAT_REMOVED="$CAT_REMOVED  - $msg ($hash)\n"
  else
    CAT_CHANGED="$CAT_CHANGED  - $msg ($hash)\n"
  fi
done < <(get_commits)

today=$(date +%Y-%m-%d)

{
  echo "# Changelog"
  echo ""
  echo "## [$LAST_TAG] - $today"
  echo ""

  if [ -n "$CAT_ADDED" ]; then
    echo "### Added"
    echo ""
    printf "$CAT_ADDED"
    echo ""
  fi

  if [ -n "$CAT_FIXED" ]; then
    echo "### Fixed"
    echo ""
    printf "$CAT_FIXED"
    echo ""
  fi

  if [ -n "$CAT_CHANGED" ]; then
    echo "### Changed"
    echo ""
    printf "$CAT_CHANGED"
    echo ""
  fi

  if [ -n "$CAT_REMOVED" ]; then
    echo "### Removed"
    echo ""
    printf "$CAT_REMOVED"
    echo ""
  fi

  if [ -z "$CAT_ADDED$CAT_FIXED$CAT_CHANGED$CAT_REMOVED" ]; then
    echo "_No changes since last tag._"
    echo ""
  fi
} > "$OUTPUT"

echo "Changelog generated: $OUTPUT"
echo "Last tag: ${LAST_TAG:-'(no tags found, used full history)'}"
echo "Entries: $(get_commits | wc -l | tr -d ' ')"
