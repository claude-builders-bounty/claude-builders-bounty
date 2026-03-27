#!/usr/bin/env bash
# changelog.sh — Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--from TAG]

set -euo pipefail

FROM_TAG="${1:-}"
OUTPUT="${2:-CHANGELOG.md}"
REPO_NAME="${REPO_NAME:-$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo .)")}"

# Get commits since last tag or all
if [[ -n "$FROM_TAG" ]]; then
  RANGE="$FROM_TAG..HEAD"
elif git describe --tags --abbrev=0 &>/dev/null; then
  LAST_TAG=$(git describe --tags --abbrev=0)
  RANGE="$LAST_TAG..HEAD"
  echo "Generating changelog since tag: $LAST_TAG"
else
  RANGE="--all"
  echo "No tags found — generating changelog for all commits"
fi

# Temporary file for raw commits
TMP=$(mktemp)
trap "rm -f $TMP" EXIT

# Fetch commits with format: hash|author|date|subject
git log $RANGE --pretty=format:"%H|%an|%ad|%s" --date=short 2>/dev/null | grep -v "^$" > "$TMP"

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"

if [[ -n "$FROM_TAG" ]]; then
  echo "## [$FROM_TAG] - $(date +%Y-%m-%d)" >> "$OUTPUT"
elif git describe --tags --abbrev=0 &>/dev/null; then
  echo "## [${LAST_TAG#v}] - $(git log -1 --format=%ad --date=short $LAST_TAG)" >> "$OUTPUT"
else
  echo "## [Unreleased]" >> "$OUTPUT"
fi
echo "" >> "$OUTPUT"

# Initialize categories
declare -A categories=(
  ["feat"]="Added"
  ["fix"]="Fixed"
  ["refactor"]="Changed"
  ["perf"]="Changed"
  ["chore"]="Changed"
  ["docs"]="Changed"
  ["test"]="Changed"
  ["ci"]="Changed"
  ["build"]="Changed"
  [" BREAKING"]="Removed"
)

declare -A entries
for cat in "Added" "Fixed" "Changed" "Removed"; do
  entries[$cat]=""
done

# Process each commit
while IFS='|' read -r hash author date subject; do
  # Skip merge commits
  [[ "$subject" == "Merge"* ]] && continue

  # Extract issue/PR reference
  refs=$(echo "$subject" | grep -oE '#[0-9]+' | sort -u | tr '\n' ' ' | sed 's/ #/, #/g' | sed 's/^, //')
  ref_str=""
  if [[ -n "$refs" ]]; then
    ref_str=" (${refs%, })"
  fi

  # Categorize
  lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  
  categorized=false
  for prefix in "feat" "fix" "refactor" "perf" "chore" "docs" "test" "ci" "build"; do
    if [[ "$lower_subject" == "$prefix:"* || "$lower_subject" == "$prefix("* ]]; then
      cat="${categories[$prefix]}"
      clean_msg=$(echo "$subject" | sed -E 's/^[a-z]+(\([^)]+\))?:\s*//')
      entries[$cat]+="- $clean_msg (@$author$ref_str)\n"
      categorized=true
      break
    fi
  done

  # Check for BREAKING CHANGE
  if [[ "$lower_subject" == *"breaking"* || "$subject" == "BREAKING"* ]]; then
    clean_msg=$(echo "$subject" | sed -E 's/^[a-z]+(\([^)]+\))?:\s*//')
    entries[Removed]+="- ⚠️ $clean_msg (@$author$ref_str)\n"
  fi

done < "$TMP"

# Write sections (only if non-empty)
for cat in "Added" "Fixed" "Changed" "Removed"; do
  if [[ -n "${entries[$cat]}" ]]; then
    echo "### $cat" >> "$OUTPUT"
    echo -e "${entries[$cat]}" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
done

echo "Changelog written to: $OUTPUT"
cat "$OUTPUT"
