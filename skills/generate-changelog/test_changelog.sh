#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Changelog Generator Test Suite ==="

TEST_DIR=$(mktemp -d)
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/changelog.sh"

trap 'rm -rf "$TEST_DIR"' EXIT

cd "$TEST_DIR"
git init -b main
git config user.name "Tester"
git config user.email "tester@example.com"

# Create dummy initial release
echo "init" > file1.txt
git add file1.txt
git commit -m "feat: initial commit with basic architecture"
git tag v1.0.0

# Create commits for unreleased
echo "feature" >> file1.txt
git commit -am "feat(auth): add OAuth2 login provider support"

echo "fix" >> file1.txt
git commit -am "fix(session): resolve token expiry bug on mobile"

echo "refactor" >> file1.txt
git commit -am "refactor(db): optimize query performance for user dashboard"

echo "removed" >> file1.txt
git commit -am "remove: drop deprecated legacy v1 rest api"

# Run generator
bash "$SCRIPT_PATH"

# Assert output exists and contains categorized entries
if [ ! -f CHANGELOG.md ]; then
  echo "❌ Error: CHANGELOG.md was not created."
  exit 1
fi

grep -q "### Added" CHANGELOG.md || (echo "❌ Missing Added section"; exit 1)
grep -q "add OAuth2 login provider support" CHANGELOG.md || (echo "❌ Missing Added commit"; exit 1)
grep -q "### Fixed" CHANGELOG.md || (echo "❌ Missing Fixed section"; exit 1)
grep -q "resolve token expiry bug on mobile" CHANGELOG.md || (echo "❌ Missing Fixed commit"; exit 1)
grep -q "### Changed" CHANGELOG.md || (echo "❌ Missing Changed section"; exit 1)
grep -q "### Removed" CHANGELOG.md || (echo "❌ Missing Removed section"; exit 1)

echo "✅ All Changelog tests passed successfully!"
