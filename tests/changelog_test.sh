#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cd "$tmp_dir"
git init -q
git config core.autocrlf false
git config user.email "test@example.invalid"
git config user.name "Changelog Test"

printf 'one\n' > file.txt
git add file.txt
git commit -q -m "feat: initial feature"
git tag v1.0.0

printf 'two\n' >> file.txt
git add file.txt
git commit -q -m "fix(parser): repair edge case"

printf 'three\n' >> file.txt
git add file.txt
git commit -q -m "remove: obsolete option"

CHANGELOG_VERSION=v1.1.0 bash "$script_dir/changelog.sh" CHANGELOG.md

grep -q "All notable changes are grouped from git commits since v1.0.0." CHANGELOG.md
grep -q "## v1.1.0" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q -- "- repair edge case" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q -- "- obsolete option" CHANGELOG.md
if grep -q "initial feature" CHANGELOG.md; then
  echo "error: changelog included commits before latest tag" >&2
  exit 1
fi

echo "changelog_test.sh passed"
