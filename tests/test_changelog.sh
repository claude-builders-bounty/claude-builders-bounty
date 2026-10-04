#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SCRIPT="$ROOT/changelog.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
assert_contains() { grep -Fq -- "$2" "$1" || fail "$1 does not contain: $2"; }

repo="$TMP/repo"
mkdir -p "$repo"
git -C "$repo" init -q
git -C "$repo" config user.email test@example.com
git -C "$repo" config user.name Tester
printf 'one\n' > "$repo/file.txt"
git -C "$repo" add file.txt
git -C "$repo" commit -qm 'feat: add first feature'
git -C "$repo" tag v1.0.0
printf 'two\n' >> "$repo/file.txt"
git -C "$repo" commit -qam 'fix: correct broken output'
printf 'three\n' >> "$repo/file.txt"
git -C "$repo" commit -qam 'refactor: simplify parser'
printf 'four\n' >> "$repo/file.txt"
git -C "$repo" commit -qam 'remove: retire legacy path'

output="$TMP/CHANGELOG.md"
"$SCRIPT" --repo "$repo" --output "$output"

assert_contains "$output" '## Added'
assert_contains "$output" '## Fixed'
assert_contains "$output" '## Changed'
assert_contains "$output" '## Removed'
assert_contains "$output" 'fix: correct broken output'
assert_contains "$output" 'refactor: simplify parser'
assert_contains "$output" 'remove: retire legacy path'

empty="$TMP/EMPTY.md"
"$SCRIPT" --repo "$repo" --since v1.0.0 --output "$empty"
assert_contains "$empty" '## Added'
assert_contains "$empty" $'- None'
if grep -Fq 'feat: add first feature' "$output"; then fail 'tagged commit leaked into post-tag changelog'; fi

manual="$TMP/MANUAL.md"
"$SCRIPT" --repo "$repo" --since v1.0.0 --output "$manual"
assert_contains "$manual" 'fix: correct broken output'

if "$SCRIPT" --repo "$TMP/missing" --output "$TMP/nope.md" >/dev/null 2>&1; then fail 'missing repo should fail'; fi

echo 'PASS: changelog generation'
