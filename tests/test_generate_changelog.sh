#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="${ROOT}/skills/generate-changelog/changelog.sh"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

cd "${TMP_DIR}"
git init -q
git config user.name "Test User"
git config user.email "test@example.invalid"

printf 'initial\n' > app.txt
git add app.txt
git commit -q -m "chore: initial commit"
git tag v0.1.0

printf 'webhook\n' >> app.txt
git add app.txt
git commit -q -m "feat: add webhook ingestion"

printf 'fix\n' >> app.txt
git add app.txt
git commit -q -m "fix: handle empty payload"

printf 'copy\n' >> app.txt
git add app.txt
git commit -q -m "docs: update dashboard copy"

printf 'remove\n' >> app.txt
git add app.txt
git commit -q -m "remove: remove legacy CSV export"

bash "${SCRIPT}" >/tmp/generate-changelog-test.log

test -f CHANGELOG.md
grep -q "since v0.1.0" CHANGELOG.md
grep -q "### Added" CHANGELOG.md
grep -q -- "- add webhook ingestion" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q -- "- handle empty payload" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q -- "- update dashboard copy" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q -- "- remove legacy CSV export" CHANGELOG.md

echo "generate changelog test passed"
