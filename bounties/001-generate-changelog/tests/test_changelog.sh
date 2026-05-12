#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
generator="$script_dir/../scripts/changelog.sh"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cd "$tmp_dir"
git init --quiet
git config user.email "test@example.com"
git config user.name "Changelog Test"

printf 'initial\n' > app.txt
git add app.txt
git commit --quiet -m "chore: initial commit"
git tag v1.0.0

printf 'feature\n' >> app.txt
git commit --quiet -am "feat: add dashboard"

printf 'fix\n' >> app.txt
git commit --quiet -am "fix: repair dashboard refresh"

printf 'docs\n' >> app.txt
git commit --quiet -am "docs: update setup guide"

printf 'remove\n' >> app.txt
git commit --quiet -am "remove obsolete option"

CHANGELOG_DATE=2026-05-12 bash "$generator" --no-fetch >/tmp/changelog-test.log

grep -q "Commits since v1.0.0" CHANGELOG.md
grep -q "### Added" CHANGELOG.md
grep -q "feat: add dashboard" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q "fix: repair dashboard refresh" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q "docs: update setup guide" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q "remove obsolete option" CHANGELOG.md

if grep -q "chore: initial commit" CHANGELOG.md; then
  echo "Tagged commit should not appear in generated changelog" >&2
  exit 1
fi

echo "changelog generator test passed"
