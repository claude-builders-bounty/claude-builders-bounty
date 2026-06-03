#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT_DIR/changelog.sh"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

assert_contains() {
  local file="$1"
  local expected="$2"

  if ! grep -Fq "$expected" "$file"; then
    echo "Expected to find: $expected"
    echo "--- $file ---"
    cat "$file"
    exit 1
  fi
}

assert_not_contains() {
  local file="$1"
  local unexpected="$2"

  if grep -Fq "$unexpected" "$file"; then
    echo "Did not expect to find: $unexpected"
    echo "--- $file ---"
    cat "$file"
    exit 1
  fi
}

init_repo() {
  local repo="$1"

  git init -q "$repo"
  git -C "$repo" config core.autocrlf false
  git -C "$repo" config user.email "test@example.com"
  git -C "$repo" config user.name "Test User"
}

commit_file() {
  local repo="$1"
  local message="$2"
  local file="$3"

  printf '%s\n' "$message" > "$repo/$file"
  git -C "$repo" add "$file"
  git -C "$repo" commit -q -m "$message"
}

test_generates_changelog_without_tags() {
  local repo="$TMP_DIR/no-tags"
  init_repo "$repo"

  commit_file "$repo" "feat: add billing export" "feature.txt"
  commit_file "$repo" "fix: repair timeout handling" "fix.txt"
  commit_file "$repo" "docs: update setup guide" "docs.txt"
  commit_file "$repo" "remove deprecated endpoint" "remove.txt"

  bash "$SCRIPT" "$repo" "$repo/CHANGELOG.md"

  assert_contains "$repo/CHANGELOG.md" "## Unreleased"
  assert_contains "$repo/CHANGELOG.md" "### Added"
  assert_contains "$repo/CHANGELOG.md" "add billing export"
  assert_contains "$repo/CHANGELOG.md" "### Fixed"
  assert_contains "$repo/CHANGELOG.md" "repair timeout handling"
  assert_contains "$repo/CHANGELOG.md" "### Changed"
  assert_contains "$repo/CHANGELOG.md" "update setup guide"
  assert_contains "$repo/CHANGELOG.md" "### Removed"
  assert_contains "$repo/CHANGELOG.md" "remove deprecated endpoint"
}

test_uses_commits_since_latest_tag() {
  local repo="$TMP_DIR/with-tag"
  init_repo "$repo"

  commit_file "$repo" "feat: old tagged feature" "old.txt"
  git -C "$repo" tag "v1.0.0"
  commit_file "$repo" "feat: add current feature" "current.txt"

  bash "$SCRIPT" "$repo" "$repo/CHANGELOG.md"

  assert_contains "$repo/CHANGELOG.md" "Changes since v1.0.0"
  assert_contains "$repo/CHANGELOG.md" "add current feature"
  assert_not_contains "$repo/CHANGELOG.md" "old tagged feature"
}

test_generates_changelog_without_tags
test_uses_commits_since_latest_tag

echo "All tests passed."
