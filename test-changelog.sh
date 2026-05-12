#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT
WORK_DIR="${TEST_ROOT}/with-tag"
NO_TAG_DIR="${TEST_ROOT}/without-tag"

mkdir -p "$WORK_DIR" "$NO_TAG_DIR"

cd "$WORK_DIR"
git init --quiet
git config user.email "test@example.com"
git config user.name "Test User"

echo "initial" > app.txt
git add app.txt
git commit --quiet -m "chore: initial release"
git tag v1.0.0

echo "feature" >> app.txt
git commit --quiet -am "feat: add export command"

echo "fix" >> app.txt
git commit --quiet -am "fix: handle empty repositories"

echo "docs" >> app.txt
git commit --quiet -am "docs: update usage notes"

echo "remove" >> app.txt
git commit --quiet -am "remove legacy config"

"$ROOT_DIR/changelog.sh"

test -f CHANGELOG.md
grep -q "## Unreleased" CHANGELOG.md
grep -q "### Added" CHANGELOG.md
grep -q -- "- add export command" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q -- "- handle empty repositories" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q -- "- update usage notes" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q -- "- remove legacy config" CHANGELOG.md

cd "$NO_TAG_DIR"
git init --quiet
git config user.email "test@example.com"
git config user.name "Test User"

echo "first" > app.txt
git add app.txt
git commit --quiet -m "feat: initial command"

"$ROOT_DIR/changelog.sh"

test -f CHANGELOG.md
grep -q "Changes from git history" CHANGELOG.md
grep -q -- "- initial command" CHANGELOG.md
