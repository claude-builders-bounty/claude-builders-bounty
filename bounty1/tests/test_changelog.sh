#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf -- $tmp_dir' EXIT

git -C "$tmp_dir" init -q
git -C "$tmp_dir" config user.email test@example.invalid
git -C "$tmp_dir" config user.name "Changelog Test"

printf 'baseline\n' >"$tmp_dir/file.txt"
git -C "$tmp_dir" add file.txt
git -C "$tmp_dir" commit -q -m 'chore: baseline'
git -C "$tmp_dir" tag v1.0.0

printf 'feature\n' >>"$tmp_dir/file.txt"
git -C "$tmp_dir" add file.txt
git -C "$tmp_dir" commit -q -m 'feat: add feature'
git -C "$tmp_dir" commit --allow-empty -q -m 'fix: correct edge case'
git -C "$tmp_dir" commit --allow-empty -q -m 'remove: remove legacy path'
git -C "$tmp_dir" commit --allow-empty -q -m 'refactor: simplify parser'

(cd "$tmp_dir" && bash "$script_dir/changelog.sh" --output generated.md)

grep -Fq '## Unreleased' "$tmp_dir/generated.md"
grep -Fq '### Added' "$tmp_dir/generated.md"
grep -Fq '### Fixed' "$tmp_dir/generated.md"
grep -Fq '### Changed' "$tmp_dir/generated.md"
grep -Fq '### Removed' "$tmp_dir/generated.md"
grep -Fq 'add feature' "$tmp_dir/generated.md"
grep -Fq 'correct edge case' "$tmp_dir/generated.md"
grep -Fq 'remove legacy path' "$tmp_dir/generated.md"
grep -Fq 'simplify parser' "$tmp_dir/generated.md"

echo 'test_changelog.sh: PASS'
