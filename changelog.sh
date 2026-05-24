#!/bin/bash
# changelog.sh - Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [since_tag]

set -e

REPO_PATH="${1:-.}"
OUTPUT_FILE="CHANGELOG.md"

cd "$REPO_PATH"

# Get the latest tag or default to last 30 commits
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
 COMMITS=$(git log "$LAST_TAG..HEAD" --pretty=format:"%s|%an" 2>/dev/null || echo "")
 HEADER="## [Unreleased] ($(date +%Y-%m-%d))"
else
 COMMITS=$(git log -30 --pretty=format:"%s|%an" 2>/dev/null || echo "")
 HEADER="## [Unreleased] ($(date +%Y-%m-%d))"
fi

# Initialize sections
declare -A sections=(
 ["Added"]=""
 ["Fixed"]=""
 ["Changed"]=""
 ["Removed"]=""
 ["Other"]=""
)

# Parse commits
while IFS='|' read -r msg author; do
 [ -z "$msg" ] && continue
 
 entry="- $msg"
 
 case "$msg" in
 feat:*|feat\!:*|feature:*)
 sections["Added"]="${sections["Added"]}\n${entry}"
 ;;
 fix:*|fix\!:*|bugfix:*)
 sections["Fixed"]="${sections["Fixed"]}\n${entry}"
 ;;
 docs:*|doc:*)
 sections["Changed"]="${sections["Changed"]}\n${entry}"
 ;;
 refactor:*|perf:*|test:*|chore:*|style:*)
 sections["Changed"]="${sections["Changed"]}\n${entry}"
 ;;
 BREAKING\ CHANGE:*|breaking:*)
 sections["Removed"]="${sections["Removed"]}\n${entry}"
 ;;
 remove:*|removed:*|delete:*|deprecat*:*)
 sections["Removed"]="${sections["Removed"]}\n${entry}"
 ;;
 *)
 sections["Other"]="${sections["Other"]}\n${entry}"
 ;;
 esac
done <<< "$COMMITS"

# Build output
{
 echo "# Changelog"
 echo ""
 echo "All notable changes to this project are documented in this file."
 echo ""
 echo "$HEADER"
 echo ""
 
 for section in "Added" "Fixed" "Changed" "Removed"; do
 if [ -n "${sections[$section]}" ]; then
 echo "### $section"
 echo -e "${sections[$section]}"
 echo ""
 fi
 done
 
 if [ -n "${sections["Other"]}" ]; then
 echo "### Other Changes"
 echo -e "${sections["Other"]}"
 echo ""
 fi
} > "$OUTPUT_FILE"

echo "Generated: $OUTPUT_FILE"
cat "$OUTPUT_FILE"