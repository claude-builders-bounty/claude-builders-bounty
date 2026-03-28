#!/usr/bin/env bash
set -euo pipefail

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
RANGE="HEAD"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="$LAST_TAG..HEAD"
fi

COMMITS=$(git log --pretty=format:'%s' $RANGE)

added=()
fixed=()
changed=()
removed=()

while IFS= read -r line; do
  l=$(echo "$line" | tr '[:upper:]' '[:lower:]')
  if [[ "$l" =~ ^feat|^add|\bcreate\b|\bintroduce\b ]]; then
    added+=("$line")
  elif [[ "$l" =~ ^fix|\bbug\b|\bpatch\b ]]; then
    fixed+=("$line")
  elif [[ "$l" =~ ^remove|\bdelete\b|\bdrop\b|\bdeprecate\b ]]; then
    removed+=("$line")
  else
    changed+=("$line")
  fi
done <<< "$COMMITS"

DATE=$(date +%F)
{
  echo "# CHANGELOG"
  echo
  echo "## [Unreleased] - $DATE"
  echo
  echo "### Added"
  for x in "${added[@]}"; do echo "- $x"; done
  echo
  echo "### Fixed"
  for x in "${fixed[@]}"; do echo "- $x"; done
  echo
  echo "### Changed"
  for x in "${changed[@]}"; do echo "- $x"; done
  echo
  echo "### Removed"
  for x in "${removed[@]}"; do echo "- $x"; done
} > CHANGELOG.md

echo "Generated CHANGELOG.md from range: ${RANGE}"
