#!/usr/bin/env bash
# generate-changelog.sh
# Generates a structured CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [output]

set -euo pipefail

OUTPUT_FILE=${1:-CHANGELOG.md}
cd "$(git rev-parse --show-toplevel)"

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project."
  echo ""

  # Get tags sorted by date descending
  mapfile -t TAGS < <(git tag --sort=-creatordate)

  if [ ${#TAGS[@]} -eq 0 ]; then
    echo "## [Unreleased]"
    echo ""
    git log --pretty=format:"- %s (%h)" --no-merges -30
    echo ""
  else
    PREV=""
    for TAG in "${TAGS[@]}"; do
      DATE=$(git log -1 --format=%ad --date=short "$TAG")
      echo "## [$TAG] - $DATE"
      echo ""
      
      if [ -n "$PREV" ]; then
        git log --pretty=format:"- %s (%h)" --no-merges "$TAG..$PREV"
      else
        git log --pretty=format:"- %s (%h)" --no-merges "$TAG"
      fi
      echo ""
      echo ""
      PREV=$TAG
    done
  fi
} > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE"
