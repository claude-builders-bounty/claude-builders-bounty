#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git -C "$tmp" init -q
git -C "$tmp" config user.email test@example.com
git -C "$tmp" config user.name "Changelog Test"

touch "$tmp/app.txt"
git -C "$tmp" add app.txt
git -C "$tmp" commit -q -m "feat: initial app"
git -C "$tmp" tag v1.0.0

printf 'feature\n' >> "$tmp/app.txt"
git -C "$tmp" add app.txt
git -C "$tmp" commit -q -m "feat: add dashboard"

printf 'bugfix\n' >> "$tmp/app.txt"
git -C "$tmp" add app.txt
git -C "$tmp" commit -q -m "fix: repair auth flow"

printf 'cleanup\n' >> "$tmp/app.txt"
git -C "$tmp" add app.txt
git -C "$tmp" commit -q -m "refactor: simplify parser"

printf 'removed\n' >> "$tmp/app.txt"
git -C "$tmp" add app.txt
git -C "$tmp" commit -q -m "remove: old adapter"

bash "$root/changelog.sh" --repo "$tmp" --output "$tmp/CHANGELOG.md" >/dev/null

grep -q "### Added" "$tmp/CHANGELOG.md"
grep -q "add dashboard" "$tmp/CHANGELOG.md"
grep -q "### Fixed" "$tmp/CHANGELOG.md"
grep -q "repair auth flow" "$tmp/CHANGELOG.md"
grep -q "### Changed" "$tmp/CHANGELOG.md"
grep -q "simplify parser" "$tmp/CHANGELOG.md"
grep -q "### Removed" "$tmp/CHANGELOG.md"
grep -q "old adapter" "$tmp/CHANGELOG.md"

echo "changelog generator test passed"
