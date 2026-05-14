#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="${ROOT_DIR}/changelog.sh"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

cd "${TMP_DIR}"
git init -q
git config user.email "test@example.com"
git config user.name "Changelog Test"

printf 'initial\n' > app.txt
git add app.txt
git commit -q -m "chore: initial release"
git tag v1.0.0

printf 'feature\n' >> app.txt
git add app.txt
git commit -q -m "feat: add export flow"

printf 'fix\n' >> app.txt
git add app.txt
git commit -q -m "fix(parser): handle empty input"

printf 'change\n' >> app.txt
git add app.txt
git commit -q -m "refactor: simplify renderer"

rm app.txt
git add app.txt
git commit -q -m "remove deprecated app file"

bash "${SCRIPT}" CHANGELOG.md

grep -q "Changes since v1.0.0" CHANGELOG.md
grep -q "### Added" CHANGELOG.md
grep -q -- "- add export flow" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q -- "- handle empty input" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q -- "- simplify renderer" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q -- "- deprecated app file" CHANGELOG.md

if grep -q "initial release" CHANGELOG.md; then
  echo "Expected commits before the latest tag to be excluded" >&2
  exit 1
fi

echo "changelog.sh regression test passed"
