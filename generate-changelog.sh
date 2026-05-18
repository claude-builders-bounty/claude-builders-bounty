#!/usr/bin/env bash
# generate-changelog.sh
# Generates a structured CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [output]

set -euo pipefail

OUTPUT_FILE=${1:-CHANGELOG.md}
# Resolve to absolute path before cd so relative paths stay relative to caller
[[ "$OUTPUT_FILE" != /* ]] && OUTPUT_FILE="$PWD/$OUTPUT_FILE"

cd "$(git rev-parse --show-toplevel)"

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project."
  echo ""

  # Tags sorted newest-to-oldest
  mapfile -t TAGS < <(git tag --sort=-creatordate)

  if [ ${#TAGS[@]} -eq 0 ]; then
    echo "## [Unreleased]"
    echo ""
    git log --pretty=format:"- %s (%h)" --no-merges -30
    echo ""
  else
    # Commits after the newest tag that haven't been released yet
    NEWEST="${TAGS[0]}"
    UNRELEASED=$(git log --pretty=format:"- %s (%h)" --no-merges "$NEWEST..HEAD")
    if [ -n "$UNRELEASED" ]; then
      echo "## [Unreleased]"
      echo ""
      echo "$UNRELEASED"
      echo ""
      echo ""
    fi

    # One section per tag, newest-to-oldest.
    # Each section covers commits from the next-older tag (exclusive) up to
    # this tag (inclusive).  The oldest tag gets all commits up to itself.
    for i in "${!TAGS[@]}"; do
      TAG="${TAGS[$i]}"
      DATE=$(git log -1 --format=%ad --date=short "$TAG")
      echo "## [$TAG] - $DATE"
      echo ""

      next_i=$((i + 1))
      if (( next_i < ${#TAGS[@]} )); then
        OLDER_TAG="${TAGS[$next_i]}"
        git log --pretty=format:"- %s (%h)" --no-merges "$OLDER_TAG..$TAG"
      else
        # Oldest tag: include everything from the very first commit
        git log --pretty=format:"- %s (%h)" --no-merges "$TAG"
      fi
      echo ""
      echo ""
    done
  fi
} > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE"
