#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cp "$repo_root/changelog.sh" "$tmpdir/changelog.sh"
cd "$tmpdir"

git init --quiet
git config user.email "fixture@example.com"
git config user.name "Fixture Test"

printf 'initial\n' > app.txt
git add app.txt
git commit --quiet -m "feat: initial app"
git tag v1.0.0

printf 'feature\n' >> app.txt
git add app.txt
git commit --quiet -m "feat: add reporting dashboard"

printf 'fix\n' >> app.txt
git add app.txt
git commit --quiet -m "fix: handle empty input"

printf 'docs\n' >> app.txt
git add app.txt
git commit --quiet -m "docs: update setup guide"

rm app.txt
git add app.txt
git commit --quiet -m "remove: delete legacy config"

output="$(bash changelog.sh --stdout --no-fetch)"

assert_contains() {
  local needle="$1"
  if [[ "$output" != *"$needle"* ]]; then
    printf 'Expected output to contain: %s\n\nActual output:\n%s\n' "$needle" "$output" >&2
    exit 1
  fi
}

assert_not_contains() {
  local needle="$1"
  if [[ "$output" == *"$needle"* ]]; then
    printf 'Expected output not to contain: %s\n\nActual output:\n%s\n' "$needle" "$output" >&2
    exit 1
  fi
}

assert_contains "_Generated from commits since v1.0.0._"
assert_contains "### Added"
assert_contains "add reporting dashboard"
assert_contains "### Fixed"
assert_contains "handle empty input"
assert_contains "### Changed"
assert_contains "update setup guide"
assert_contains "### Removed"
assert_contains "delete legacy config"
assert_not_contains "initial app"

printf 'changelog fixture test passed\n'
