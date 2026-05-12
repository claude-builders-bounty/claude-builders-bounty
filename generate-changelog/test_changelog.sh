#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$TMP_DIR"
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

echo "initial" > app.txt
git add app.txt
git commit -qm "feat: initial app"
git tag v1.0.0

echo "login" >> app.txt
git add app.txt
git commit -qm "feat(auth): add login flow"

echo "bugfix" >> app.txt
git add app.txt
git commit -qm "fix: repair redirect bug"

echo "cleanup" >> app.txt
git add app.txt
git commit -qm "remove deprecated setting"

bash "$SCRIPT_DIR/changelog.sh" --dry-run > output.md

grep -q "## \\[Unreleased\\]" output.md
grep -q "### Added" output.md
grep -q "add login flow" output.md
grep -q "### Fixed" output.md
grep -q "repair redirect bug" output.md
grep -q "### Removed" output.md
grep -q "deprecated setting" output.md

echo "All changelog tests passed."
