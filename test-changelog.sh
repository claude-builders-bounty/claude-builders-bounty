#!/usr/bin/env bash
set -euo pipefail
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
git -C "$root" init -q
git -C "$root" config user.email test@example.invalid
git -C "$root" config user.name Test
touch "$root/file"
git -C "$root" add file && git -C "$root" commit -qm 'initial'
git -C "$root" tag v1.0.0
git -C "$root" commit --allow-empty -qm 'feat: add export'
git -C "$root" commit --allow-empty -qm 'fix: handle empty input'
git -C "$root" commit --allow-empty -qm 'remove: obsolete flag'
git -C "$root" commit --allow-empty -qm 'docs: explain usage'
"$(dirname "$0")/changelog.sh" "$root/CHANGELOG.md" "$root"
grep -Fq -- '- feat: add export' "$root/CHANGELOG.md"
grep -Fq -- '## Fixed' "$root/CHANGELOG.md"
grep -Fq -- '- remove: obsolete flag' "$root/CHANGELOG.md"
grep -Fq -- '- docs: explain usage' "$root/CHANGELOG.md"
! grep -Fxq -- '- ' "$root/CHANGELOG.md"
echo 'changelog test: PASS'
