#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
cp changelog.sh "$tmpdir/"
cd "$tmpdir"

git init -q
git config user.email test@example.com
git config user.name Tester

echo base > app.txt
git add app.txt
git commit -q -m 'chore: base'
git tag v0.1.0

echo feature >> app.txt
git add app.txt
git commit -q -m 'feat: add export button'

echo fix >> app.txt
git add app.txt
git commit -q -m 'fix: repair edge case'

git rm -q app.txt
git commit -q -m 'remove: drop obsolete file'

./changelog.sh OUT.md >/tmp/changelog-test-output.txt

grep -q 'Generated from git history since v0.1.0' OUT.md
grep -q '## Added' OUT.md
grep -q 'feat: add export button' OUT.md
grep -q '## Fixed' OUT.md
grep -q 'fix: repair edge case' OUT.md
grep -q '## Removed' OUT.md
grep -q 'remove: drop obsolete file' OUT.md

echo 'changelog.sh smoke test passed'
