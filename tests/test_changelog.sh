#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

git -C "$tmp_dir" init -q
git -C "$tmp_dir" config user.email "test@example.com"
git -C "$tmp_dir" config user.name "Test User"

printf 'initial\n' > "$tmp_dir/file.txt"
git -C "$tmp_dir" add file.txt
git -C "$tmp_dir" commit -q -m "chore: initial release"
git -C "$tmp_dir" tag v1.0.0

printf 'feature\n' >> "$tmp_dir/file.txt"
git -C "$tmp_dir" commit -am "feat: add export button" -q

printf 'fix\n' >> "$tmp_dir/file.txt"
git -C "$tmp_dir" commit -am "fix: correct empty state" -q

printf 'change\n' >> "$tmp_dir/file.txt"
git -C "$tmp_dir" commit -am "refactor: simplify parser" -q

printf 'remove\n' >> "$tmp_dir/file.txt"
git -C "$tmp_dir" commit -am "remove: legacy flag" -q

output="$tmp_dir/CHANGELOG.md"
bash "$repo_root/changelog.sh" --repo "$tmp_dir" --output "$output" --version "Test"

grep -q 'Source range: `v1.0.0..HEAD`' "$output"
grep -q '### Added' "$output"
grep -q 'add export button' "$output"
grep -q '### Fixed' "$output"
grep -q 'correct empty state' "$output"
grep -q '### Changed' "$output"
grep -q 'simplify parser' "$output"
grep -q '### Removed' "$output"
grep -q 'legacy flag' "$output"
if grep -q 'initial release' "$output"; then
  echo "included commits before the latest tag" >&2
  exit 1
fi

echo "changelog generator test passed"
