#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Cuts commits since the LAST TAG (falls back to all history when repo has no tags).
# Zero dependencies: bash + git + python3 only.
#
# Usage:
#   bash changelog.sh [repo_path] [output.md]
#   bash changelog.sh                    # current repo -> CHANGELOG.md
#   bash changelog.sh /path/to/repo out.md
set -euo pipefail

REPO="${1:-.}"
OUT="${2:-$REPO/CHANGELOG.md}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TAG="$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$TAG" ]; then
  RANGE="$TAG..HEAD"
  VERSION="$TAG → next (unreleased)"
else
  RANGE="HEAD"
  VERSION="Unreleased"
fi

git -C "$REPO" log "$RANGE" --pretty=format:'%h %s' --no-merges \
  | python3 "$DIR/changelog_gen.py" --stdin --version "$VERSION" -o "$OUT"

echo "changelog.sh: wrote $OUT (range: $RANGE)"
