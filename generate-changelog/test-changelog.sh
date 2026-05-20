#!/usr/bin/env bash
set -euo pipefail

script_path="${1:-./changelog.sh}"
script_path="$(cd "$(dirname "$script_path")" && pwd)/$(basename "$script_path")"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cd "$tmpdir"
git init -q
git config user.email "test@example.com"
git config user.name "Changelog Test"

printf 'initial\n' > file.txt
git add file.txt
git commit -q -m "feat: initial release"
git tag v1.0.0

printf 'feature\n' >> file.txt
git add file.txt
git commit -q -m "feat: add dashboard"

printf 'fix\n' >> file.txt
git add file.txt
git commit -q -m "fix: repair login"

printf 'docs\n' >> file.txt
git add file.txt
git commit -q -m "docs: update usage guide"

printf 'remove\n' >> file.txt
git add file.txt
git commit -q -m "remove: drop legacy config"

bash "$script_path" CHANGELOG.md >/dev/null

assert_contains() {
  local expected="$1"
  if ! grep -Fq -- "$expected" CHANGELOG.md; then
    echo "Expected generated changelog to contain: $expected" >&2
    echo "--- CHANGELOG.md ---" >&2
    cat CHANGELOG.md >&2
    exit 1
  fi
}

assert_not_contains() {
  local unexpected="$1"
  if grep -Fq -- "$unexpected" CHANGELOG.md; then
    echo "Generated changelog unexpectedly contained: $unexpected" >&2
    echo "--- CHANGELOG.md ---" >&2
    cat CHANGELOG.md >&2
    exit 1
  fi
}

assert_contains "Generated"
assert_contains "since v1.0.0"
assert_contains "### Added"
assert_contains "- add dashboard"
assert_contains "### Fixed"
assert_contains "- repair login"
assert_contains "### Changed"
assert_contains "- update usage guide"
assert_contains "### Removed"
assert_contains "- drop legacy config"
assert_not_contains "initial release"

echo "changelog smoke test passed"
