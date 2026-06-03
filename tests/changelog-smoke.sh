#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

cp "$repo_root/changelog.sh" "$work_dir/changelog.sh"
cd "$work_dir"

git init -q
git config user.email "test@example.com"
git config user.name "Changelog Test"

printf 'seed\n' >demo.txt
git add demo.txt
git commit -q -m "feat: initial release"
git tag v1.0.0

printf 'feature\n' >>demo.txt
git add demo.txt
git commit -q -m "feat: add dashboard"

printf 'fix\n' >>demo.txt
git add demo.txt
git commit -q -m "fix: handle empty input"

printf 'docs\n' >>demo.txt
git add demo.txt
git commit -q -m "docs: update usage"

printf 'remove\n' >>demo.txt
git add demo.txt
git commit -q -m "remove: legacy flag"

bash changelog.sh CHANGELOG.md >/dev/null

grep -q "Commit range: since v1.0.0" CHANGELOG.md
grep -q "### Added" CHANGELOG.md
grep -q "add dashboard" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q "handle empty input" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q "update usage" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q "legacy flag" CHANGELOG.md

echo "changelog smoke test passed"
