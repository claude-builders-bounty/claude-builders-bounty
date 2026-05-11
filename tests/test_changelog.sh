#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

cd "$work_dir"
git init -q
git config user.email "test@example.com"
git config user.name "Changelog Test"

printf 'base\n' >app.txt
git add app.txt
git commit -q -m "chore: initial baseline"
git tag v0.1.0

printf 'feature\n' >>app.txt
git add app.txt
git commit -q -m "feat: add export command"

printf 'fix\n' >>app.txt
git add app.txt
git commit -q -m "fix: handle empty tag ranges"

printf 'docs\n' >>app.txt
git add app.txt
git commit -q -m "docs: update setup instructions"

printf 'remove\n' >>app.txt
git add app.txt
git commit -q -m "remove: delete deprecated flag"

bash "${repo_root}/changelog.sh" CHANGELOG.md >/tmp/changelog-test-output.txt

grep -q "Generated from commits since v0.1.0" CHANGELOG.md
grep -q "### Added" CHANGELOG.md
grep -q "feat: add export command" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q "fix: handle empty tag ranges" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q "docs: update setup instructions" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q "remove: delete deprecated flag" CHANGELOG.md

echo "All changelog tests passed."
