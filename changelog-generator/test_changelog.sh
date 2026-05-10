#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cd "$tmpdir"
git init -q
git config user.name "Changelog Test"
git config user.email "changelog-test@example.com"

echo "one" > file.txt
git add file.txt
git commit -q -m "feat: add initial feature"
git tag v1.0.0

echo "two" >> file.txt
git commit -am "fix: repair tagged bug" -q

echo "three" >> file.txt
git commit -am "docs: update setup guide" -q

echo "four" >> file.txt
git commit -am "remove: delete old flow" -q

bash "$repo_root/changelog.sh" >/tmp/changelog-test-output.txt

grep -q "since v1.0.0" CHANGELOG.md
grep -q "fix: repair tagged bug" CHANGELOG.md
grep -q "docs: update setup guide" CHANGELOG.md
grep -q "remove: delete old flow" CHANGELOG.md
! grep -q "feat: add initial feature" CHANGELOG.md

echo "changelog generator test passed"
