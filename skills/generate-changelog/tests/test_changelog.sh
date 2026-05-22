#!/usr/bin/env bash
set -euo pipefail

script_path="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/changelog.sh"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

git -C "$tmp_dir" init -q
git -C "$tmp_dir" config user.email "test@example.com"
git -C "$tmp_dir" config user.name "Test User"

printf 'base\n' > "$tmp_dir/file.txt"
git -C "$tmp_dir" add file.txt
git -C "$tmp_dir" commit -q -m "chore: initial release"
git -C "$tmp_dir" tag v1.0.0

printf 'feature\n' >> "$tmp_dir/file.txt"
git -C "$tmp_dir" add file.txt
git -C "$tmp_dir" commit -q -m "feat: add export command"

printf 'fix\n' >> "$tmp_dir/file.txt"
git -C "$tmp_dir" add file.txt
git -C "$tmp_dir" commit -q -m "fix: repair parser edge case"

printf 'change\n' >> "$tmp_dir/file.txt"
git -C "$tmp_dir" add file.txt
git -C "$tmp_dir" commit -q -m "refactor: update categorizer"

rm "$tmp_dir/file.txt"
git -C "$tmp_dir" add file.txt
git -C "$tmp_dir" commit -q -m "remove: drop legacy fixture"

bash "$script_path" --repo "$tmp_dir" --output "$tmp_dir/CHANGELOG.md" --no-fetch >/dev/null

grep -q 'Source: commits since v1.0.0' "$tmp_dir/CHANGELOG.md"
grep -q '### Added' "$tmp_dir/CHANGELOG.md"
grep -q 'add export command' "$tmp_dir/CHANGELOG.md"
grep -q '### Fixed' "$tmp_dir/CHANGELOG.md"
grep -q 'repair parser edge case' "$tmp_dir/CHANGELOG.md"
grep -q '### Changed' "$tmp_dir/CHANGELOG.md"
grep -q 'update categorizer' "$tmp_dir/CHANGELOG.md"
grep -q '### Removed' "$tmp_dir/CHANGELOG.md"
grep -q 'drop legacy fixture' "$tmp_dir/CHANGELOG.md"

if grep -q 'initial release' "$tmp_dir/CHANGELOG.md"; then
  echo "tagged commit leaked into post-tag changelog" >&2
  exit 1
fi

echo "changelog generator tests passed"
