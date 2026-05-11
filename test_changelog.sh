#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/generate-changelog-test.XXXXXX")"

cleanup() {
  rm -rf "$work_dir"
}
trap cleanup EXIT

assert_contains() {
  file="$1"
  expected="$2"

  if ! grep -Fq -- "$expected" "$file"; then
    echo "Expected to find: $expected" >&2
    echo "In file: $file" >&2
    echo "--- file contents ---" >&2
    cat "$file" >&2
    echo "---------------------" >&2
    exit 1
  fi
}

assert_not_contains() {
  file="$1"
  unexpected="$2"

  if grep -Fq -- "$unexpected" "$file"; then
    echo "Did not expect to find: $unexpected" >&2
    echo "In file: $file" >&2
    echo "--- file contents ---" >&2
    cat "$file" >&2
    echo "---------------------" >&2
    exit 1
  fi
}

init_repo() {
  repo_path="$1"
  mkdir -p "$repo_path"
  cd "$repo_path"
  git init -q
  git config user.email "test@example.com"
  git config user.name "Generate Changelog Test"
}

commit_change() {
  message="$1"
  file_name="$2"
  content="$3"

  printf '%s\n' "$content" >> "$file_name"
  git add "$file_name"
  git commit -q -m "$message"
}

no_tag_repo="$work_dir/no-tag"
init_repo "$no_tag_repo"
commit_change "feat: add onboarding flow" "app.txt" "added"
commit_change "fix: repair changelog grouping" "app.txt" "fixed"
commit_change "docs: update setup notes" "docs.txt" "changed"
commit_change "remove: delete legacy option" "legacy.txt" "removed"

bash "$repo_root/changelog.sh" "$no_tag_repo/CHANGELOG.md" >/dev/null

assert_contains "$no_tag_repo/CHANGELOG.md" "# Changelog"
assert_contains "$no_tag_repo/CHANGELOG.md" "_Generated from Git history from all commits._"
assert_contains "$no_tag_repo/CHANGELOG.md" "### Added"
assert_contains "$no_tag_repo/CHANGELOG.md" "- add onboarding flow"
assert_contains "$no_tag_repo/CHANGELOG.md" "### Fixed"
assert_contains "$no_tag_repo/CHANGELOG.md" "- repair changelog grouping"
assert_contains "$no_tag_repo/CHANGELOG.md" "### Changed"
assert_contains "$no_tag_repo/CHANGELOG.md" "- update setup notes"
assert_contains "$no_tag_repo/CHANGELOG.md" "### Removed"
assert_contains "$no_tag_repo/CHANGELOG.md" "- delete legacy option"

tagged_repo="$work_dir/tagged"
init_repo "$tagged_repo"
commit_change "feat: add released feature" "app.txt" "released"
git tag v1.0.0
commit_change "fix: repair post-release bug" "app.txt" "post-release"
commit_change "chore: update package metadata" "package.txt" "metadata"

bash "$repo_root/changelog.sh" "$tagged_repo/CHANGELOG.md" >/dev/null

assert_contains "$tagged_repo/CHANGELOG.md" "_Generated from Git history since v1.0.0._"
assert_not_contains "$tagged_repo/CHANGELOG.md" "- add released feature"
assert_contains "$tagged_repo/CHANGELOG.md" "- repair post-release bug"
assert_contains "$tagged_repo/CHANGELOG.md" "- update package metadata"

echo "All changelog generator tests passed."
