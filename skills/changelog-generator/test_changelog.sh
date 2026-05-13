#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/changelog.sh"

assert_contains() {
  local file="$1"
  local expected="$2"
  if ! grep -Fq -- "$expected" "$file"; then
    echo "Expected to find: $expected" >&2
    echo "--- file ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

assert_not_contains() {
  local file="$1"
  local unexpected="$2"
  if grep -Fq -- "$unexpected" "$file"; then
    echo "Did not expect to find: $unexpected" >&2
    echo "--- file ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

new_repo() {
  local repo
  repo="$(mktemp -d)"
  git init -q "$repo"
  git -C "$repo" config user.email "test@example.com"
  git -C "$repo" config user.name "Test User"
  printf 'initial\n' > "$repo/file.txt"
  git -C "$repo" add file.txt
  git -C "$repo" commit -q -m "chore: initial commit"
  echo "$repo"
}

commit_msg() {
  local repo="$1"
  local msg="$2"
  printf '%s\n' "$msg" >> "$repo/file.txt"
  git -C "$repo" add file.txt
  git -C "$repo" commit -q -m "$msg"
}

test_tagged_range() {
  local repo out
  repo="$(new_repo)"
  git -C "$repo" tag v1.0.0
  commit_msg "$repo" "feat: add import wizard"
  commit_msg "$repo" "fix(api): handle timeout"
  commit_msg "$repo" "remove legacy endpoint"
  commit_msg "$repo" "misc cleanup"
  out="$repo/CHANGELOG.md"

  "$SCRIPT" --repo "$repo" --output "$out" >/dev/null

  assert_contains "$out" "## 1.0.0"
  assert_contains "$out" "### Added"
  assert_contains "$out" "- add import wizard"
  assert_contains "$out" "### Fixed"
  assert_contains "$out" "- handle timeout"
  assert_contains "$out" "### Removed"
  assert_contains "$out" "- remove legacy endpoint"
  assert_contains "$out" "### Other"
  assert_contains "$out" "- misc cleanup"
  assert_not_contains "$out" "initial commit"
}

test_no_tag_uses_all_history() {
  local repo out
  repo="$(new_repo)"
  commit_msg "$repo" "feat: add first feature"
  out="$repo/NOTES.md"

  "$SCRIPT" --repo "$repo" --output "$out" >/dev/null

  assert_contains "$out" "## Unreleased"
  assert_contains "$out" "- initial commit"
  assert_contains "$out" "- add first feature"
  assert_contains "$out" "_2 commits covering all history_"
}

test_reverse_order() {
  local repo out first_line second_line
  repo="$(new_repo)"
  git -C "$repo" tag v1.0.0
  commit_msg "$repo" "feat: older feature"
  commit_msg "$repo" "feat: newer feature"
  out="$repo/RELEASE.md"

  "$SCRIPT" --repo "$repo" --output "$out" --reverse >/dev/null

  first_line="$(grep -n -- "- older feature" "$out" | cut -d: -f1)"
  second_line="$(grep -n -- "- newer feature" "$out" | cut -d: -f1)"
  if [ "$first_line" -ge "$second_line" ]; then
    echo "--reverse did not preserve oldest-first order" >&2
    cat "$out" >&2
    exit 1
  fi
}

test_tagged_range
test_no_tag_uses_all_history
test_reverse_order

echo "All changelog generator tests passed"
