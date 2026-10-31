#!/usr/bin/env bash
set -euo pipefail

# Ensure we are inside a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: Not a git repository" >&2
  exit 1
fi

# Determine the most recent tag; if none exists, use the whole history
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG=$(git describe --tags --abbrev=0)
  RANGE="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

# Collect commits in the range
mapfile -t COMMITS < <(git log $RANGE --pretty=format:"%h %s")

# Prepare sections for the changelog
declare -A sections=(
  ["Added"]=""
  ["Fixed"]=""
  ["Changed"]=""
  ["Removed"]=""
)

# Helper to append a line to a section
append_to_section() {
  local section="$1"
  local line="$2"
  sections[$section]+="$line"$'\n'
}

# Classify each commit based on conventional prefixes
for line in "${COMMITS[@]}"; do
  hash=${line%% *}
  msg=${line#* }
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  if [[ $lower == feat:* || $lower == feature:* ]]; then
    cat="Added"
  elif [[ $lower == fix:* ]]; then
    cat="Fixed"
  elif [[ $lower == chore:* || $lower == refactor:* || $lower == style:* ]]; then
    cat="Changed"
  elif [[ $lower == remove:* || $lower == del:* || $lower == delete:* ]]; then
    cat="Removed"
  else
    cat="Changed"
  fi
  # Build markdown line with a link to the commit (GitHub repository placeholder)
  commit_link="[\`${hash}\`](https://github.com/${GITHUB_REPOSITORY:-user/repo}/commit/${hash})"
  append_to_section "$cat" "- ${msg} (${commit_link})"
done

# Write the CHANGELOG.md file
{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased]"
  echo ""
  for sec in Added Fixed Changed Removed; do
    if [[ -n ${sections[$sec]} ]]; then
      echo "### $sec"
      echo "${sections[$sec]}"
    fi
  done
} > CHANGELOG.md

echo "CHANGELOG.md generated successfully."
