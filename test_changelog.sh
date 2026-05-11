#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp_repo="$(mktemp -d)"
trap 'rm -rf "$tmp_repo"' EXIT

git -C "$tmp_repo" init -q
git -C "$tmp_repo" config core.autocrlf false
git -C "$tmp_repo" config user.email "test@example.com"
git -C "$tmp_repo" config user.name "Changelog Test"

printf 'base\n' > "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "chore: initial commit"
git -C "$tmp_repo" tag v1.0.0

printf 'feature\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "feat: add export button"

printf 'fix\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "fix: handle empty git tag list"

printf 'change\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "docs: update setup guide"

printf 'remove\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "remove: drop legacy option"

bash "$script_dir/changelog.sh" "$tmp_repo" "$tmp_repo/CHANGELOG.md" >/dev/null

grep -q "## Added" "$tmp_repo/CHANGELOG.md"
grep -q "feat: add export button" "$tmp_repo/CHANGELOG.md"
grep -q "## Fixed" "$tmp_repo/CHANGELOG.md"
grep -q "fix: handle empty git tag list" "$tmp_repo/CHANGELOG.md"
grep -q "## Changed" "$tmp_repo/CHANGELOG.md"
grep -q "docs: update setup guide" "$tmp_repo/CHANGELOG.md"
grep -q "## Removed" "$tmp_repo/CHANGELOG.md"
grep -q "remove: drop legacy option" "$tmp_repo/CHANGELOG.md"
if grep -q "chore: initial commit" "$tmp_repo/CHANGELOG.md"; then
  echo "Tagged commit should not appear in generated changelog." >&2
  exit 1
fi

echo "test_changelog.sh passed"
