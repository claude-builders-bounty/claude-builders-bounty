#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

git -C "$tmp_dir" init -q
git -C "$tmp_dir" config user.email "smoke@example.com"
git -C "$tmp_dir" config user.name "Smoke Test"
git -C "$tmp_dir" config core.autocrlf false

commit_change() {
  local message="$1"
  local contents="$2"

  printf '%s\n' "$contents" >> "$tmp_dir/app.txt"
  git -C "$tmp_dir" add app.txt
  git -C "$tmp_dir" commit -q -m "$message"
}

commit_change "feat: old feature before tag" "old feature"
git -C "$tmp_dir" tag v1.0.0

commit_change "feat: add dashboard filters" "filters"
commit_change "fix(auth): handle expired sessions" "sessions"
commit_change "refactor: simplify billing service" "billing"
commit_change "remove: delete legacy import path" "legacy"

cp "$repo_root/changelog.sh" "$tmp_dir/changelog.sh"

(
  cd "$tmp_dir"
  bash ./changelog.sh >/dev/null
)

output="$tmp_dir/CHANGELOG.md"

assert_contains() {
  local expected="$1"

  if ! grep -Fq -- "$expected" "$output"; then
    echo "Expected CHANGELOG.md to contain: $expected" >&2
    echo "--- CHANGELOG.md ---" >&2
    cat "$output" >&2
    exit 1
  fi
}

assert_not_contains() {
  local unexpected="$1"

  if grep -Fq -- "$unexpected" "$output"; then
    echo "Expected CHANGELOG.md not to contain: $unexpected" >&2
    echo "--- CHANGELOG.md ---" >&2
    cat "$output" >&2
    exit 1
  fi
}

assert_contains "Generated from git commits after v1.0.0"
assert_contains "### Added"
assert_contains "- add dashboard filters"
assert_contains "### Fixed"
assert_contains "- handle expired sessions"
assert_contains "### Changed"
assert_contains "- simplify billing service"
assert_contains "### Removed"
assert_contains "- delete legacy import path"
assert_not_contains "old feature before tag"

echo "Smoke test passed. Sample output:"
cat "$output"
