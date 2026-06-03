#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
changelog_script="${repo_root}/changelog.sh"

assert_contains() {
  local file="$1"
  local expected="$2"

  if ! grep -Fq -- "$expected" "$file"; then
    echo "Expected to find: ${expected}" >&2
    echo "--- ${file} ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

make_commit() {
  local message="$1"
  local contents="$2"

  printf "%s\n" "$contents" >> fixture.txt
  git add fixture.txt
  git commit -q -m "$message"
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cd "$tmpdir"
git init -q
git config user.email "test@example.com"
git config user.name "Changelog Test"

make_commit "feat: initial fixture" "initial"
bash "$changelog_script" >/dev/null
assert_contains CHANGELOG.md "_Changes from all commits_"
assert_contains CHANGELOG.md "### Added"
assert_contains CHANGELOG.md "- feat: initial fixture"

git tag v1.0.0
make_commit "feat(ui): add dashboard" "added"
make_commit "fix: repair export crash" "fixed"
make_commit "refactor: change parser layout" "changed"
make_commit "remove: delete legacy flag" "removed"

bash "$changelog_script" >/dev/null
assert_contains CHANGELOG.md "_Changes since v1.0.0_"
assert_contains CHANGELOG.md "- feat(ui): add dashboard"
assert_contains CHANGELOG.md "- fix: repair export crash"
assert_contains CHANGELOG.md "- refactor: change parser layout"
assert_contains CHANGELOG.md "- remove: delete legacy flag"

git tag v2.0.0
bash "$changelog_script" >/dev/null
assert_contains CHANGELOG.md "_Changes since v2.0.0_"
assert_contains CHANGELOG.md "No changes since the last git tag."

echo "changelog.sh tests passed"
