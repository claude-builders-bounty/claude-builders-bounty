#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
script="$script_dir/../scripts/changelog.sh"
tmp_repo="$(mktemp -d)"
trap 'rm -rf "$tmp_repo"' EXIT

git -C "$tmp_repo" init -q
git -C "$tmp_repo" config user.email "test@example.com"
git -C "$tmp_repo" config user.name "Changelog Test"

printf 'first\n' > "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "feat: initial release"
git -C "$tmp_repo" tag v1.0.0

printf 'second\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "fix: correct parser edge case"

printf 'third\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "remove: drop legacy option"

bash "$script" --repo "$tmp_repo" --version v1.1.0

grep -q "## v1.1.0" "$tmp_repo/CHANGELOG.md"
grep -q "### Fixed" "$tmp_repo/CHANGELOG.md"
grep -q "fix: correct parser edge case" "$tmp_repo/CHANGELOG.md"
grep -q "### Removed" "$tmp_repo/CHANGELOG.md"
grep -q "remove: drop legacy option" "$tmp_repo/CHANGELOG.md"

echo "changelog_test.sh passed"
