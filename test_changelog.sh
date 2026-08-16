#!/usr/bin/env bash

set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/changelog-test.XXXXXX")"
cleanup() {
  rm -rf "$temp_dir"
}
trap cleanup EXIT

assert_contains() {
  needle="$1"
  file="$2"
  if ! grep -F -- "$needle" "$file" >/dev/null 2>&1; then
    echo "Expected to find '$needle' in $file" >&2
    cat "$file" >&2
    exit 1
  fi
}

assert_not_contains() {
  needle="$1"
  file="$2"
  if grep -F -- "$needle" "$file" >/dev/null 2>&1; then
    echo "Did not expect to find '$needle' in $file" >&2
    cat "$file" >&2
    exit 1
  fi
}

commit_file() {
  repo="$1"
  file_name="$2"
  message="$3"
  printf '%s\n' "$message" > "$repo/$file_name"
  git -C "$repo" add "$file_name"
  git -C "$repo" commit -qm "$message"
}

tagged_repo="$temp_dir/tagged-repo"
mkdir -p "$tagged_repo"
git init -q "$tagged_repo"
git -C "$tagged_repo" config user.name "Changelog Test"
git -C "$tagged_repo" config user.email "changelog-test@example.invalid"
commit_file "$tagged_repo" README.md "chore: initial release"
git -C "$tagged_repo" tag v1.0.0
commit_file "$tagged_repo" added.txt "feat: add export endpoint"
commit_file "$tagged_repo" fixed.txt "fix: handle empty input"
commit_file "$tagged_repo" changed.txt "refactor: simplify parser"
commit_file "$tagged_repo" removed.txt "remove: obsolete flag"

tagged_output="$temp_dir/tagged.md"
bash "$script_dir/changelog.sh" --repo "$tagged_repo" --output "$tagged_output" --no-date >/dev/null
assert_contains 'Generated from git history since `v1.0.0`.' "$tagged_output"
assert_contains '### Added' "$tagged_output"
assert_contains '### Fixed' "$tagged_output"
assert_contains '### Changed' "$tagged_output"
assert_contains '### Removed' "$tagged_output"
assert_contains 'add export endpoint' "$tagged_output"
assert_contains 'handle empty input' "$tagged_output"
assert_contains 'simplify parser' "$tagged_output"
assert_contains 'obsolete flag' "$tagged_output"
assert_not_contains 'initial release' "$tagged_output"

untagged_repo="$temp_dir/untagged-repo"
mkdir -p "$untagged_repo"
git init -q "$untagged_repo"
git -C "$untagged_repo" config user.name "Changelog Test"
git -C "$untagged_repo" config user.email "changelog-test@example.invalid"
commit_file "$untagged_repo" README.md "chore: bootstrap project"
commit_file "$untagged_repo" first.txt "add: first feature"

untagged_output="$temp_dir/untagged.md"
bash "$script_dir/changelog.sh" --repo "$untagged_repo" --output "$untagged_output" --no-date >/dev/null
assert_contains 'Generated from git history since `repository root`.' "$untagged_output"
assert_contains 'bootstrap project' "$untagged_output"
assert_contains 'first feature' "$untagged_output"

help_output="$temp_dir/help.txt"
bash "$script_dir/changelog.sh" --help > "$help_output"
assert_contains 'Generate a structured CHANGELOG.md' "$help_output"

echo "PASS: changelog generation, categorisation, no-tag fallback, and help output"
