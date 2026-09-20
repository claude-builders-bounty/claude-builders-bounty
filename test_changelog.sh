#!/usr/bin/env bash
set -euo pipefail

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
git -C "$tmp" init -q
git -C "$tmp" config user.email test@example.invalid
git -C "$tmp" config user.name Test
touch "$tmp/README"
git -C "$tmp" add README && git -C "$tmp" commit -qm 'chore: initialize'
echo feature >> "$tmp/README" && git -C "$tmp" commit -qam 'feat: add feature'
echo fix >> "$tmp/README" && git -C "$tmp" commit -qam 'fix: correct behavior'
echo remove >> "$tmp/README" && git -C "$tmp" commit -qam 'remove: old behavior'

cp changelog.sh "$tmp/changelog.sh"
chmod +x "$tmp/changelog.sh"
(cd "$tmp" && ./changelog.sh)
grep -q '^### Added$' "$tmp/CHANGELOG.md"
grep -q '^### Fixed$' "$tmp/CHANGELOG.md"
grep -q '^### Removed$' "$tmp/CHANGELOG.md"
grep -q 'feat: add feature' "$tmp/CHANGELOG.md"
echo "changelog smoke test passed"
