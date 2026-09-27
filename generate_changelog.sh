#!/bin/bash
# Generate CHANGELOG.md from git history

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE=${LAST_TAG:+${LAST_TAG}..HEAD}

echo "# Changelog" > CHANGELOG.md
echo "" >> CHANGELOG.md

get_commits() { git log $RANGE --pretty=format:"%s" | grep -i "^$1"; }

write_section() {
  local title=$1
  local pattern=$2
  local commits=$(get_commits "$pattern")
  if [ ! -z "$commits" ]; then
    echo "## $title" >> CHANGELOG.md
    echo "$commits" | sed 's/^/ - /' >> CHANGELOG.md
    echo "" >> CHANGELOG.md
  fi
}

write_section "Added" "feat"
write_section "Fixed" "fix"
write_section "Changed" "refactor|perf|style"
write_section "Removed" "chore(remove)"

echo "Changelog generated successfully."