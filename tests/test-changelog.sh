#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

assert_contains() {
  local file="$1"
  local expected="$2"

  grep -Fq -- "$expected" "$file" || {
    printf 'Expected to find %s in %s\n' "$expected" "$file" >&2
    sed -n '1,160p' "$file" >&2
    exit 1
  }
}

assert_not_contains() {
  local file="$1"
  local unexpected="$2"

  if grep -Fq -- "$unexpected" "$file"; then
    printf 'Did not expect to find %s in %s\n' "$unexpected" "$file" >&2
    sed -n '1,160p' "$file" >&2
    exit 1
  fi
}

commit_change() {
  local message="$1"
  local content="$2"

  printf '%s\n' "$content" >>app.txt
  git add app.txt
  git commit -q -m "$message"
}

setup_repo() {
  local path="$1"

  mkdir -p "$path"
  cd "$path"
  git init -q
  git config user.email test@example.com
  git config user.name "Changelog Test"
}

test_since_latest_tag() {
  local repo="$TMP_DIR/tagged"
  setup_repo "$repo"

  commit_change "chore: initial release" "base"
  git tag v1.0.0
  commit_change "feat: add billing dashboard" "feature"
  commit_change "fix: resolve invoice rounding bug" "fix"
  commit_change "remove deprecated export flag" "remove"

  CHANGELOG_FETCH_TAGS=0 bash "$ROOT_DIR/changelog.sh" >/tmp/changelog-test.log

  assert_contains CHANGELOG.md 'Changes since `v1.0.0`. Commit count: 3.'
  assert_contains CHANGELOG.md '### Added'
  assert_contains CHANGELOG.md '- add billing dashboard'
  assert_contains CHANGELOG.md '### Fixed'
  assert_contains CHANGELOG.md '- resolve invoice rounding bug'
  assert_contains CHANGELOG.md '### Removed'
  assert_contains CHANGELOG.md '- remove deprecated export flag'
  assert_not_contains CHANGELOG.md 'initial release'
}

test_without_tags() {
  local repo="$TMP_DIR/untagged"
  setup_repo "$repo"

  commit_change "docs: add usage notes" "docs"

  CHANGELOG_FETCH_TAGS=0 bash "$ROOT_DIR/changelog.sh" >/tmp/changelog-test.log

  assert_contains CHANGELOG.md 'Changes from the full repository history because no git tag was found. Commit count: 1.'
  assert_contains CHANGELOG.md '- add usage notes'
}

test_since_latest_tag
test_without_tags

printf 'All changelog tests passed.\n'
