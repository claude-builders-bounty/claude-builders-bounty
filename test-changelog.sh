#!/usr/bin/env bash
set -euo pipefail

repo="$(mktemp -d)"
trap 'rm -rf "$repo"' EXIT

git -C "$repo" init -q
git -C "$repo" config user.email "test@example.com"
git -C "$repo" config user.name "Changelog Test"

printf 'initial\n' > "$repo/file.txt"
git -C "$repo" add file.txt
git -C "$repo" commit -m "chore: initial commit" >/dev/null
git -C "$repo" tag v0.1.0

printf 'feature\n' >> "$repo/file.txt"
git -C "$repo" commit -am "feat: add export command" >/dev/null

printf 'fix\n' >> "$repo/file.txt"
git -C "$repo" commit -am "fix: handle empty commit range" >/dev/null

printf 'change\n' >> "$repo/file.txt"
git -C "$repo" commit -am "docs: refresh usage notes" >/dev/null

printf 'removed\n' >> "$repo/file.txt"
git -C "$repo" commit -am "remove: drop deprecated flag" >/dev/null

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$script_dir/changelog.sh" --repo "$repo" --output "$repo/CHANGELOG.md" >/dev/null

grep -q "Generated from git history since v0.1.0" "$repo/CHANGELOG.md"
grep -q "### Added" "$repo/CHANGELOG.md"
grep -q "feat: add export command" "$repo/CHANGELOG.md"
grep -q "### Fixed" "$repo/CHANGELOG.md"
grep -q "fix: handle empty commit range" "$repo/CHANGELOG.md"
grep -q "### Changed" "$repo/CHANGELOG.md"
grep -q "docs: refresh usage notes" "$repo/CHANGELOG.md"
grep -q "### Removed" "$repo/CHANGELOG.md"
grep -q "remove: drop deprecated flag" "$repo/CHANGELOG.md"

echo "changelog generator test passed"
