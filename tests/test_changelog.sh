#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$TMP_DIR"
git init -q
git config user.email test@example.com
git config user.name "Changelog Test"

printf 'one\n' > app.txt
git add app.txt
git commit -q -m 'feat: add first feature'
git tag v1.0.0

printf 'two\n' >> app.txt
git add app.txt
git commit -q -m 'fix: repair saved state'

printf 'docs\n' > docs.txt
git add docs.txt
git commit -q -m 'docs: update usage notes'

printf 'old\n' > old.txt
git add old.txt
git commit -q -m 'remove: drop legacy file'

"$SCRIPT_DIR/changelog.sh" CHANGELOG.md >/tmp/changelog-test.out

grep -F 'Generated from commits since tag `v1.0.0`.' CHANGELOG.md
grep -F '### Added' CHANGELOG.md
grep -F -- '- No entries.' CHANGELOG.md
grep -F '### Fixed' CHANGELOG.md
grep -F -- '- fix: repair saved state' CHANGELOG.md
grep -F '### Changed' CHANGELOG.md
grep -F -- '- docs: update usage notes' CHANGELOG.md
grep -F '### Removed' CHANGELOG.md
grep -F -- '- remove: drop legacy file' CHANGELOG.md

if grep -Fq 'feat: add first feature' CHANGELOG.md; then
  echo 'tagged commits should not be included in generated changelog' >&2
  exit 1
fi

echo 'changelog generator smoke test passed'