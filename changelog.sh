#!/usr/bin/env bash
# generate-changelog — structured CHANGELOG.md from git history since last tag
# Portable: bash 3.2+ / macOS / Linux
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

OUT="${1:-CHANGELOG.md}"
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER_NOTE="Changes since \`${LAST_TAG}\`"
else
  RANGE="HEAD"
  HEADER_NOTE="All commits (no tags found)"
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
COUNT=0

append_line() {
  # $1 = var name, $2 = text
  local var="$1"
  local text="$2"
  local cur
  eval "cur=\${$var}"
  if [ -n "$cur" ]; then
    eval "$var=\"\$cur
- \$text\""
  else
    eval "$var=\"- \$text\""
  fi
}

classify() {
  local s="$1"
  local lower
  lower="$(printf '%s' "$s" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat\(*|feat:*|feature\(*|feature:*|add\(*|add:*)
      append_line ADDED "$s" ;;
    fix\(*|fix:*|bug\(*|bugfix:*|hotfix\(*|hotfix:*|patch\(*|patch:*)
      append_line FIXED "$s" ;;
    remove\(*|remove:*|delete\(*|delete:*|drop\(*|drop:*|deprecate*)
      append_line REMOVED "$s" ;;
    chore\(*|chore:*|refactor\(*|refactor:*|perf\(*|perf:*|style\(*|style:*|docs\(*|docs:*|ci\(*|ci:*|build\(*|build:*|change\(*|change:*|update\(*|update:*)
      append_line CHANGED "$s" ;;
    add\ *|added\ *|introduce*|create\ *|implement*)
      append_line ADDED "$s" ;;
    fix\ *|fixed\ *|bugfix*|hotfix\ *|patch\ *)
      append_line FIXED "$s" ;;
    remove\ *|removed\ *|delete\ *|drop\ *)
      append_line REMOVED "$s" ;;
    change\ *|changed\ *|update\ *|updated\ *|improve*|bump\ *|refactor\ *|chore\ *)
      append_line CHANGED "$s" ;;
    *)
      append_line CHANGED "$s" ;;
  esac
}

while IFS= read -r s; do
  [ -z "$s" ] && continue
  COUNT=$((COUNT + 1))
  classify "$s"
done <<EOF
$(git log "$RANGE" --pretty=format:'%s' --no-merges)
EOF

or_none() {
  if [ -n "$1" ]; then printf '%s\n' "$1"; else echo "- _(none)_"; fi
}

TODAY="$(date -u +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)"
{
  echo "# Changelog"
  echo
  echo "## [${TODAY}] — unreleased"
  echo
  echo "_${HEADER_NOTE}_"
  echo
  echo "### Added"
  or_none "$ADDED"
  echo
  echo "### Fixed"
  or_none "$FIXED"
  echo
  echo "### Changed"
  or_none "$CHANGED"
  echo
  echo "### Removed"
  or_none "$REMOVED"
  echo
} > "$OUT"

echo "Wrote $OUT ($COUNT commits in range ${RANGE})"
