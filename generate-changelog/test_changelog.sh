#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp_repo="$(mktemp -d)"
trap 'rm -rf "$tmp_repo"' EXIT

cd "$tmp_repo"
git init -q
git config user.email "test@example.com"
git config user.name "Changelog Test"

printf 'hello\n' > app.txt
git add app.txt
git commit -q -m "feat: add app shell"
git tag v0.1.0

printf 'fix\n' >> app.txt
git add app.txt
git commit -q -m "fix: repair login redirect"

printf 'docs\n' >> app.txt
git add app.txt
git commit -q -m "docs: update setup notes"

rm app.txt
git add app.txt
git commit -q -m "remove: drop obsolete sample file"

bash "$script_dir/changelog.sh" --dry-run > CHANGELOG.md

grep -q "Commit range: v0.1.0..HEAD" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q "repair login redirect" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q "update setup notes" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md
grep -q "drop obsolete sample file" CHANGELOG.md

echo "All changelog tests passed."
