#!/bin/bash
# changelog.sh - Generate a structured CHANGELOG.md from git history

set -e

# Get the latest git tag (or empty if none)
latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Get commits since the latest tag (or all if no tag)
if [ -z "$latest_tag" ]; then
  commits=$(git log --pretty=format:"%H%x01%s%x01%b%x01%an%x01%ad" --date=short)
else
  commits=$(git log "$latest_tag"..HEAD --pretty=format:"%H%x01%s%x01%b%x01%an%x01%ad" --date=short)
fi

# Prepare changelog sections
added=()
fixed=()
changed=()
removed=()

# Categorize commits by keywords in subject or body
while IFS=$'\x01' read -r hash subject body author date; do
  # Normalize to lowercase for matching
  lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  lower_body=$(echo "$body" | tr '[:upper:]' '[:lower:]')

  if echo "$lower_subject $lower_body" | grep -qE '\b(add|added|feature|implement|new)\b'; then
    added+=("- $subject ($hash)")
  elif echo "$lower_subject $lower_body" | grep -qE '\b(fix|fixed|bug|patch|error|issue)\b'; then
    fixed+=("- $subject ($hash)")
  elif echo "$lower_subject $lower_body" | grep -qE '\b(change|changed|update|updated|improve|improved|refactor)\b'; then
    changed+=("- $subject ($hash)")
  elif echo "$lower_subject $lower_body" | grep -qE '\b(remove|removed|delete|deleted|drop)\b'; then
    removed+=("- $subject ($hash)")
  fi
done <<< "$commits"

# Output CHANGELOG.md
{
  echo "# Changelog"
  echo
  echo "## Unreleased"
  echo

  if [ ${#added[@]} -gt 0 ]; then
    echo "### Added"
    for item in "${added[@]}"; do
      echo "$item"
    done
    echo
  fi

  if [ ${#fixed[@]} -gt 0 ]; then
    echo "### Fixed"
    for item in "${fixed[@]}"; do
      echo "$item"
    done
    echo
  fi

  if [ ${#changed[@]} -gt 0 ]; then
    echo "### Changed"
    for item in "${changed[@]}"; do
      echo "$item"
    done
    echo
  fi

  if [ ${#removed[@]} -gt 0 ]; then
    echo "### Removed"
    for item in "${removed[@]}"; do
      echo "$item"
    done
    echo
  fi

} > CHANGELOG.md
