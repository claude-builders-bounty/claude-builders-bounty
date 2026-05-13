#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

cd "$WORK_DIR"
git init --quiet
git config user.email "test@example.com"
git config user.name "Test User"

printf "initial\n" > app.txt
git add app.txt
git commit --quiet -m "chore: initial commit"
git tag v1.0.0

printf "feature\n" >> app.txt
git add app.txt
git commit --quiet -m "feat: add export button"

printf "bugfix\n" >> app.txt
git add app.txt
git commit --quiet -m "fix: resolve export crash"

printf "changed\n" >> app.txt
git add app.txt
git commit --quiet -m "docs: update setup guide"

printf "removed\n" >> app.txt
git add app.txt
git commit --quiet -m "remove deprecated flag"

bash "$SCRIPT_DIR/changelog.sh" --no-fetch --output CHANGELOG.md >/tmp/changelog-smoke-test.log

grep -q "Generated on .* using commits since v1.0.0" CHANGELOG.md
grep -q "### Added" CHANGELOG.md
grep -q "add export button" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q "resolve export crash" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q "update setup guide" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q "remove deprecated flag" CHANGELOG.md

echo "changelog smoke test passed"
