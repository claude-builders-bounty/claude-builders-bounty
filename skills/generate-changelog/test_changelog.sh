#!/usr/bin/env bash
# Self-contained test: builds a throwaway git repo with tags + conventional
# commits, runs changelog.sh, and asserts the output is categorized correctly.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"
git init -q
git config user.email t@t.t
git config user.name test

echo a > a.txt; git add .; git commit -qm "feat: initial feature"
git tag v1.0.0

echo b > b.txt; git add .; git commit -qm "feat: add export button"
echo c > c.txt; git add .; git commit -qm "fix: correct off-by-one in pager"
echo d > d.txt; git add .; git commit -qm "refactor: simplify parser"
echo e > e.txt; git add .; git commit -qm "remove: drop legacy v1 endpoint"
echo f > f.txt; git add .; git commit -qm "Update the README wording"

bash "$HERE/changelog.sh" --version 1.1.0 >/dev/null

echo "----- generated CHANGELOG.md -----"
cat CHANGELOG.md
echo "----------------------------------"

fail=0
grep -q "## 1.1.0" CHANGELOG.md || { echo "FAIL: version header missing"; fail=1; }
grep -q "### Added"   CHANGELOG.md || { echo "FAIL: Added section missing"; fail=1; }
grep -q "### Fixed"   CHANGELOG.md || { echo "FAIL: Fixed section missing"; fail=1; }
grep -q "### Changed" CHANGELOG.md || { echo "FAIL: Changed section missing"; fail=1; }
grep -q "### Removed" CHANGELOG.md || { echo "FAIL: Removed section missing"; fail=1; }
grep -q "add export button" CHANGELOG.md || { echo "FAIL: feat not categorized"; fail=1; }
grep -q "off-by-one"        CHANGELOG.md || { echo "FAIL: fix not categorized"; fail=1; }
grep -q "simplify parser"   CHANGELOG.md || { echo "FAIL: refactor not categorized"; fail=1; }
grep -q "legacy v1 endpoint" CHANGELOG.md || { echo "FAIL: remove not categorized"; fail=1; }
# v1.0.0 commit must NOT appear (it is before the tag).
grep -q "initial feature" CHANGELOG.md && { echo "FAIL: pre-tag commit leaked in"; fail=1; }

if [[ $fail -eq 0 ]]; then echo "ALL TESTS PASSED"; else echo "TESTS FAILED"; exit 1; fi
