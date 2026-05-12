#!/usr/bin/env bash
set -euo pipefail

fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT
script_path="$(cd -P "$(dirname "$0")" && pwd)/changelog.sh"

git init "$fixture" >/dev/null
cd "$fixture"
git config user.name "Changelog Test"
git config user.email "changelog-test@example.com"

echo "one" > file.txt
git add file.txt
git commit -m "feat: add first feature" >/dev/null
git tag v1.0.0

echo "two" >> file.txt
git add file.txt
git commit -m "fix: correct totals" >/dev/null

echo "three" >> file.txt
git add file.txt
git commit -m "remove: deprecated option" >/dev/null

bash "$script_path" >/dev/null

grep -q "Unreleased changes since v1.0.0" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q "fix: correct totals" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q "remove: deprecated option" CHANGELOG.md

echo "generate-changelog tests passed"
