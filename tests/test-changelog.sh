#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cd "$tmp_dir"
git init --quiet
git config user.name "Changelog Test"
git config user.email "changelog-test@example.com"

echo "baseline" > app.txt
git add app.txt
git commit --quiet -m "chore: baseline"
git tag v1.0.0

echo "feature" >> app.txt
git commit --quiet -am "feat: add export command"

echo "fix" >> app.txt
git commit --quiet -am "fix(parser): handle empty commit list"

echo "change" >> app.txt
git commit --quiet -am "refactor: simplify category routing"

echo "remove" >> app.txt
git commit --quiet -am "remove: drop deprecated flag"

"$repo_root/changelog.sh" >/tmp/changelog-test-output.txt

grep -F "## Unreleased" CHANGELOG.md
grep -F "_Generated since v1.0.0._" CHANGELOG.md
grep -F "### Added" CHANGELOG.md
grep -F -- "- add export command" CHANGELOG.md
grep -F "### Fixed" CHANGELOG.md
grep -F -- "- handle empty commit list" CHANGELOG.md
grep -F "### Changed" CHANGELOG.md
grep -F -- "- simplify category routing" CHANGELOG.md
grep -F "### Removed" CHANGELOG.md
grep -F -- "- drop deprecated flag" CHANGELOG.md

echo "changelog test passed"
