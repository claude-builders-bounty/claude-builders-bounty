#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git -C "$tmp" init -q
git -C "$tmp" config user.email "test@example.com"
git -C "$tmp" config user.name "Test User"

printf 'initial\n' > "$tmp/app.txt"
git -C "$tmp" add app.txt
git -C "$tmp" commit -q -m "chore: initial release"
git -C "$tmp" tag v1.0.0

printf 'feature\n' >> "$tmp/app.txt"
git -C "$tmp" commit -qam "feat: add billing dashboard"
printf 'fix\n' >> "$tmp/app.txt"
git -C "$tmp" commit -qam "fix: resolve invoice rounding"
printf 'docs\n' >> "$tmp/app.txt"
git -C "$tmp" commit -qam "docs: update setup guide"
printf 'remove\n' >> "$tmp/app.txt"
git -C "$tmp" commit -qam "remove deprecated webhook endpoint"

bash "$root/changelog.sh" --repo "$tmp" --output "$tmp/CHANGELOG.md"

grep -q "Commits since \`v1.0.0\`" "$tmp/CHANGELOG.md"
grep -q "### Added" "$tmp/CHANGELOG.md"
grep -q "feat: add billing dashboard" "$tmp/CHANGELOG.md"
grep -q "### Fixed" "$tmp/CHANGELOG.md"
grep -q "fix: resolve invoice rounding" "$tmp/CHANGELOG.md"
grep -q "### Changed" "$tmp/CHANGELOG.md"
grep -q "docs: update setup guide" "$tmp/CHANGELOG.md"
grep -q "### Removed" "$tmp/CHANGELOG.md"
grep -q "remove deprecated webhook endpoint" "$tmp/CHANGELOG.md"

python3 -m py_compile "$root/scripts/generate_changelog.py"
echo "CHANGELOG generator test passed"
