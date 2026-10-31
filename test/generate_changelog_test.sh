#!/usr/bin/env bash
set -euo pipefail

# Create a temporary git repository
TMPDIR=$(mktemp -d)
cd "$TMPDIR"

git init -q
git config user.email "test@example.com"
git config user.name "Test User"

echo "first" > file.txt
git add file.txt
git commit -qm "feat: initial feature"

echo "second" >> file.txt
git commit -am "fix: correct typo"

# Run the changelog script from the repository root (assumed to be mounted at $PWD/../..)
# Adjust the path if the test location changes.
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/generate-changelog.sh"
"$SCRIPT_PATH"

# Verify that CHANGELOG.md contains expected sections and messages
if ! grep -q "### Added" CHANGELOG.md; then
  echo "Missing Added section" >&2
  exit 1
fi
if ! grep -q "initial feature" CHANGELOG.md; then
  echo "Missing initial feature entry" >&2
  exit 1
fi
if ! grep -q "### Fixed" CHANGELOG.md; then
  echo "Missing Fixed section" >&2
  exit 1
fi
if ! grep -q "correct typo" CHANGELOG.md; then
  echo "Missing fix entry" >&2
  exit 1
fi

echo "All tests passed."
