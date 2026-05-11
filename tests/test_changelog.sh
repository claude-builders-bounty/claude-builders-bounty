#!/usr/bin/env bash
set -euo pipefail

script_path="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/scripts/changelog.sh"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

git -C "$tmpdir" init --quiet
git -C "$tmpdir" config user.email "test@example.com"
git -C "$tmpdir" config user.name "Changelog Test"

printf 'initial\n' > "$tmpdir/README.md"
git -C "$tmpdir" add README.md
git -C "$tmpdir" commit --quiet -m "chore: initial release"
git -C "$tmpdir" tag v0.1.0

printf 'feature\n' >> "$tmpdir/README.md"
git -C "$tmpdir" add README.md
git -C "$tmpdir" commit --quiet -m "feat: add project dashboard"

printf 'fix\n' >> "$tmpdir/README.md"
git -C "$tmpdir" add README.md
git -C "$tmpdir" commit --quiet -m "fix: handle empty project list"

printf 'change\n' >> "$tmpdir/README.md"
git -C "$tmpdir" add README.md
git -C "$tmpdir" commit --quiet -m "refactor: simplify project query"

printf 'remove\n' >> "$tmpdir/README.md"
git -C "$tmpdir" add README.md
git -C "$tmpdir" commit --quiet -m "remove deprecated project flag"

bash "$script_path" --repo "$tmpdir" --output "$tmpdir/CHANGELOG.md" --version v0.2.0

grep -q "Changes since \`v0.1.0\`" "$tmpdir/CHANGELOG.md"
grep -q "### Added" "$tmpdir/CHANGELOG.md"
grep -q "add project dashboard" "$tmpdir/CHANGELOG.md"
grep -q "### Fixed" "$tmpdir/CHANGELOG.md"
grep -q "handle empty project list" "$tmpdir/CHANGELOG.md"
grep -q "### Changed" "$tmpdir/CHANGELOG.md"
grep -q "simplify project query" "$tmpdir/CHANGELOG.md"
grep -q "### Removed" "$tmpdir/CHANGELOG.md"
grep -q "remove deprecated project flag" "$tmpdir/CHANGELOG.md"

echo "changelog generator test passed"
