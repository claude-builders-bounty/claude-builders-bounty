#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="${SCRIPT_DIR}/changelog.sh"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"

git init -q
git config user.email "test@example.com"
git config user.name "AIOS Test"

echo "initial" > file.txt
git add file.txt
git commit -q -m "initial commit"
git tag v1.0.0

echo "feature" >> file.txt
git add file.txt
git commit -q -m "feat: add export support"

echo "fix" >> file.txt
git add file.txt
git commit -q -m "fix: repair export formatting"

echo "docs" >> file.txt
git add file.txt
git commit -q -m "docs: update usage notes"

echo "old" > old.txt
git add old.txt
git commit -q -m "remove: legacy output mode"

bash "$GENERATOR"

test -f CHANGELOG.md

grep -q '^## Added$' CHANGELOG.md
grep -q 'feat: add export support' CHANGELOG.md

grep -q '^## Fixed$' CHANGELOG.md
grep -q 'fix: repair export formatting' CHANGELOG.md

grep -q '^## Changed$' CHANGELOG.md
grep -q 'docs: update usage notes' CHANGELOG.md

grep -q '^## Removed$' CHANGELOG.md
grep -q 'remove: legacy output mode' CHANGELOG.md

if grep -q 'initial commit' CHANGELOG.md; then
  echo "FAIL: commit before latest tag was included"
  exit 1
fi

echo "PASS: changelog generator acceptance test"