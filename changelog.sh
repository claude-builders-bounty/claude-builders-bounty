#!/usr/bin/env bash
# changelog.sh - Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [tag]

set -e

TAG=${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")]
COMMITS=$(git log --oneline ${TAG}..HEAD 2>/dev/null || git log --oneline -100)

declare -A categories
categories[Added]=""
categories[Fixed]=""
categories[Changed]=""
categories[Removed]=""

while IFS= read -r line; do
  subject=$(echo "$line" | sed 's/^[0-9a-f]* //')
  type="Changed"
  
  if echo "$subject" | grep -qiE "^(feat|add|new)"; then
    type="Added"
  elif echo "$subject" | grep -qiE "^(fix|bug|patch)"; then
    type="Fixed"
  elif echo "$subject" | grep -qiE "^(remove|delete|deprec)"; then
    type="Removed"
  elif echo "$subject" | grep -qiE "^(refactor|restructure)"; then
    type="Changed"
  fi
  
  categories[$type]+="- $subject"$'\n'
done <<< "$COMMITS"

cat << 'EOF'
# Changelog

All notable changes to this project are documented in this file.

EOF

for cat in Added Fixed Changed Removed; do
  if [[ -n "${categories[$cat]}" ]]; then
    echo "## $cat"
    echo ""
    echo -n "${categories[$cat]}"
    echo ""
  fi
done
