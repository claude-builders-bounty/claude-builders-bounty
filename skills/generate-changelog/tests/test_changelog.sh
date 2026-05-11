#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script_path="$skill_dir/changelog.sh"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

assert_contains() {
  local expected="$1"
  local file="$2"

  if ! grep -Fq -- "$expected" "$file"; then
    echo "Expected to find: $expected" >&2
    echo "--- $file ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

assert_not_contains() {
  local unexpected="$1"
  local file="$2"

  if grep -Fq -- "$unexpected" "$file"; then
    echo "Did not expect to find: $unexpected" >&2
    echo "--- $file ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

commit_file() {
  local filename="$1"
  local contents="$2"
  local message="$3"

  printf '%s\n' "$contents" > "$filename"
  git add "$filename"
  git commit -q -m "$message"
}

cd "$tmp_dir"
git init -q
git config user.email "test@example.com"
git config user.name "Changelog Test"

commit_file "initial.txt" "initial" "Initial release"
git tag v0.1.0
commit_file "feature.txt" "feature" "feat(api): add token refresh"
commit_file "fix.txt" "fix" "fix: handle empty git history"
commit_file "docs.txt" "docs" "docs: document setup"
commit_file "old.txt" "removed" "remove legacy endpoint"

bash "$script_path" --output CHANGELOG.md

assert_contains "# Changelog" CHANGELOG.md
assert_contains "## Unreleased -" CHANGELOG.md
assert_contains '_Generated from `v0.1.0..HEAD`._' CHANGELOG.md
assert_contains "### Added" CHANGELOG.md
assert_contains "- add token refresh" CHANGELOG.md
assert_contains "### Fixed" CHANGELOG.md
assert_contains "- handle empty git history" CHANGELOG.md
assert_contains "### Changed" CHANGELOG.md
assert_contains "- document setup" CHANGELOG.md
assert_contains "### Removed" CHANGELOG.md
assert_contains "- remove legacy endpoint" CHANGELOG.md
assert_not_contains "Initial release" CHANGELOG.md

echo "All changelog tests passed."
