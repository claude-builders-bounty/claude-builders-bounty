#!/usr/bin/env bash
# test_changelog.sh — Automated test suite for changelog.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANGELOG_SH="${SCRIPT_DIR}/changelog.sh"
TEMP_DIR=$(mktemp -d)

trap 'rm -rf "$TEMP_DIR"' EXIT

echo "=== Running Changelog Generator Tests ==="

cd "$TEMP_DIR"
git init -b main >/dev/null 2>&1
git config user.email "ci@example.com"
git config user.name "CI Bot"

# 1. Test empty / initial commit
echo "file 1" > file.txt && git add file.txt && git commit -m "chore: setup repo" >/dev/null
git tag v1.0.0

# 2. Add commits representing each category
echo "file 2" >> file.txt && git add file.txt && git commit -m "feat(api): add new REST endpoints" >/dev/null
echo "file 3" >> file.txt && git add file.txt && git commit -m "fix(auth): fix session expiration bug" >/dev/null
echo "file 4" >> file.txt && git add file.txt && git commit -m "refactor(db): streamline query execution" >/dev/null
echo "file 5" >> file.txt && git add file.txt && git commit -m "remove(v1): remove deprecated legacy router" >/dev/null
echo "file 6" >> file.txt && git add file.txt && git commit -m "chore: update dependencies" >/dev/null

bash "$CHANGELOG_SH" --output TEST_CHANGELOG.md

# Assertions
echo "Verifying output categories..."
grep -q "### Added" TEST_CHANGELOG.md || { echo "FAIL: Missing Added section"; exit 1; }
grep -q "add new REST endpoints" TEST_CHANGELOG.md || { echo "FAIL: Missing feat entry"; exit 1; }

grep -q "### Fixed" TEST_CHANGELOG.md || { echo "FAIL: Missing Fixed section"; exit 1; }
grep -q "fix session expiration bug" TEST_CHANGELOG.md || { echo "FAIL: Missing fix entry"; exit 1; }

grep -q "### Changed" TEST_CHANGELOG.md || { echo "FAIL: Missing Changed section"; exit 1; }
grep -q "streamline query execution" TEST_CHANGELOG.md || { echo "FAIL: Missing refactor entry"; exit 1; }

grep -q "### Removed" TEST_CHANGELOG.md || { echo "FAIL: Missing Removed section"; exit 1; }
grep -q "remove deprecated legacy router" TEST_CHANGELOG.md || { echo "FAIL: Missing remove entry"; exit 1; }

echo "✅ All changelog generator test assertions passed!"
