#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cd "$tmp"
git init -q
git config user.email test@example.com
git config user.name "Test User"

echo "initial" > app.txt
git add app.txt
git commit -q -m "chore: initial release"
git tag v1.0.0

echo "feature" >> app.txt
git add app.txt
git commit -q -m "feat: add export flow"

echo "fix" >> app.txt
git add app.txt
git commit -q -m "fix: repair login redirect"

echo "docs" >> app.txt
git add app.txt
git commit -q -m "docs: update setup guide"

echo "removed" >> app.txt
git add app.txt
git commit -q -m "remove: drop legacy endpoint"

bash "$script_dir/changelog.sh" --dry-run > CHANGELOG.md

grep -q "Generated from git history since v1.0.0" CHANGELOG.md
grep -q "### Added" CHANGELOG.md
grep -q "add export flow" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q "repair login redirect" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q "update setup guide" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q "drop legacy endpoint" CHANGELOG.md

printf 'test_changelog.sh: ok\n'
