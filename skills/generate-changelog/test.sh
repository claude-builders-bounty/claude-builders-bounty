#!/usr/bin/env bash
# Builds a temp repo with a tag + mixed commits and asserts categorisation.
set -euo pipefail
d="$(mktemp -d)"; trap 'rm -rf "$d"' EXIT
here="$(cd "$(dirname "$0")" && pwd)"
cd "$d"; git init -q; git config user.email t@t; git config user.name t
git commit -q --allow-empty -m "feat: old feature"; git tag v1.0.0
git commit -q --allow-empty -m "feat(api): add login"
git commit -q --allow-empty -m "fix: crash on start"
git commit -q --allow-empty -m "refactor: tidy modules"
git commit -q --allow-empty -m "remove legacy endpoint"
bash "$here/changelog.sh" -v 1.1.0 >/dev/null
grep -q '### Added' CHANGELOG.md && grep -q 'add login' CHANGELOG.md
grep -q '### Fixed' CHANGELOG.md && grep -q 'crash on start' CHANGELOG.md
grep -q '### Changed' CHANGELOG.md && grep -q 'tidy modules' CHANGELOG.md
grep -q '### Removed' CHANGELOG.md && grep -q 'legacy endpoint' CHANGELOG.md
! grep -q 'old feature' CHANGELOG.md
echo "ALL TESTS PASSED"
