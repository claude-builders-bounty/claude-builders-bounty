#!/bin/bash
# changelog.sh — 从 git 历史自动生成 CHANGELOG.md
# Usage: bash changelog.sh [--since <tag>]

set -e

SINCE=""
if [ "$1" = "--since" ] && [ -n "$2" ]; then
  SINCE="$2"
elif git describe --tags --abbrev=0 2>/dev/null; then
  SINCE=$(git describe --tags --abbrev=0)
fi

if [ -z "$SINCE" ]; then
  echo "No tags found. Generating changelog from all commits..."
  LOG=$(git log --pretty=format:"%s||%h||%an" --no-merges)
else
  echo "Generating changelog since tag: $SINCE"
  LOG=$(git log "$SINCE..HEAD" --pretty=format:"%s||%h||%an" --no-merges)
fi

if [ -z "$LOG" ]; then
  echo "No new commits found."
  exit 0
fi

ADDED=(); FIXED=(); CHANGED=(); REMOVED=()
while IFS= read -r line; do
  msg=$(echo "$line" | cut -d'|' -f1)
  hash=$(echo "$line" | cut -d'|' -f2)
  author=$(echo "$line" | cut -d'|' -f3)
  lmsg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  entry="$msg ($hash, $author)"

  if echo "$lmsg" | grep -qE '^(feat|add|new|feature)'; then
    ADDED+=("$entry")
  elif echo "$lmsg" | grep -qE '^(fix|bug|hotfix|patch)'; then
    FIXED+=("$entry")
  elif echo "$lmsg" | grep -qE '^(remove|drop|delete|deprecate)'; then
    REMOVED+=("$entry")
  else
    CHANGED+=("$entry")
  fi
done <<< "$LOG"

DATE=$(date +%Y-%m-%d)
OUT="# Changelog\n\n## [$DATE]\n"

write_section() {
  local title="$1"; shift
  local items=("$@")
  if [ ${#items[@]} -gt 0 ]; then
    OUT+="\n### $title\n"
    for item in "${items[@]}"; do
      OUT+="- $item\n"
    done
  fi
}

write_section "Added" "${ADDED[@]}"
write_section "Fixed" "${FIXED[@]}"
write_section "Changed" "${CHANGED[@]}"
write_section "Removed" "${REMOVED[@]}"

echo -e "$OUT" > CHANGELOG.md
echo "✅ CHANGELOG.md generated with ${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed commits."
