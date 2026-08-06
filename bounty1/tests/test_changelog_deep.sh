#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf -- "$tmp_dir"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_contains() {
  local needle="$1"
  local file="$2"
  grep -Fq -- "$needle" "$file" || fail "missing [$needle] in $file"
}

assert_not_contains() {
  local needle="$1"
  local file="$2"
  if grep -Fq -- "$needle" "$file"; then
    fail "unexpected [$needle] in $file"
  fi
}

assert_fails() {
  local label="$1"
  shift
  if "$@"; then
    fail "expected failure: $label"
  fi
}

init_repo() {
  local repo="$1"
  mkdir -p "$repo"
  git -C "$repo" init -q
  git -C "$repo" config user.email test@example.invalid
  git -C "$repo" config user.name "Changelog Deep Test"
}

commit_file() {
  local repo="$1"
  local message="$2"
  local content="$3"
  printf '%s\n' "$content" >>"$repo/history.txt"
  git -C "$repo" add history.txt
  git -C "$repo" commit -q -m "$message"
}

tagged_repo="$tmp_dir/tagged repo"
init_repo "$tagged_repo"
commit_file "$tagged_repo" "chore: baseline" "baseline"
git -C "$tagged_repo" tag v1.0.0
commit_file "$tagged_repo" "feat(ui): add dashboard" "dashboard"
commit_file "$tagged_repo" "fix: correct edge case" "fixed"
commit_file "$tagged_repo" "remove: remove legacy parser" "removed"
commit_file "$tagged_repo" "docs: update instructions" "docs"
commit_file "$tagged_repo" "Fix link to docs" "fix-link"
commit_file "$tagged_repo" "support: add Linux support" "linux"
commit_file "$tagged_repo" "DELETE: delete old flag" "deleted"
git -C "$tagged_repo" remote add origin git@github.com:sample-owner/sample-repo.git

output_file="$tagged_repo/build dir/CHANGELOG.md"
(cd "$tagged_repo" && bash "$script_dir/changelog.sh" --output "build dir/CHANGELOG.md" --version 1.2.0)

assert_contains '## 1.2.0' "$output_file"
assert_contains '### Added' "$output_file"
assert_contains '### Fixed' "$output_file"
assert_contains '### Changed' "$output_file"
assert_contains '### Removed' "$output_file"
assert_contains 'add dashboard' "$output_file"
assert_contains 'correct edge case' "$output_file"
assert_contains 'Fix link to docs' "$output_file"
assert_contains 'update instructions' "$output_file"
assert_contains 'remove legacy parser' "$output_file"
assert_contains 'delete old flag' "$output_file"
assert_contains 'add Linux support' "$output_file"
assert_contains 'https://github.com/sample-owner/sample-repo/commit/' "$output_file"
assert_not_contains 'baseline' "$output_file"
[[ "$(grep -c '^### ' "$output_file")" -eq 4 ]] || fail 'expected exactly four category headings'
[[ "$(grep -c '^- ' "$output_file")" -eq 7 ]] || fail 'expected exactly seven generated entries'

# Explicit --since must produce the same post-tag set.
explicit_output="$tagged_repo/explicit.md"
(cd "$tagged_repo" && bash "$script_dir/changelog.sh" --since v1.0.0 --output explicit.md)
assert_contains 'add dashboard' "$explicit_output"
assert_not_contains 'baseline' "$explicit_output"

# HTTPS GitHub remotes should generate the same commit-link format.
git -C "$tagged_repo" remote set-url origin https://github.com/sample-owner/sample-repo.git
https_output="$tagged_repo/https.md"
(cd "$tagged_repo" && bash "$script_dir/changelog.sh" --output https.md)
assert_contains 'https://github.com/sample-owner/sample-repo/commit/' "$https_output"

# A non-GitHub remote must fall back to short hashes instead of malformed URLs.
git -C "$tagged_repo" remote set-url origin https://example.invalid/project.git
local_output="$tagged_repo/local.md"
(cd "$tagged_repo" && bash "$script_dir/changelog.sh" --output local.md)
assert_contains ' (`' "$local_output"
assert_not_contains 'github.com' "$local_output"

# No-tag repositories use the full history.
notag_repo="$tmp_dir/no-tag"
init_repo "$notag_repo"
commit_file "$notag_repo" "feat: first release" "first"
commit_file "$notag_repo" "fix: first release bug" "bug"
notag_output="$notag_repo/generated.md"
(cd "$notag_repo" && bash "$script_dir/changelog.sh" --output generated.md)
assert_contains 'first release' "$notag_output"
assert_contains 'first release bug' "$notag_output"
assert_contains 'no reachable tag' "$notag_output"

# An empty post-tag range still produces a valid four-section document.
empty_repo="$tmp_dir/empty"
init_repo "$empty_repo"
commit_file "$empty_repo" "chore: only commit" "only"
git -C "$empty_repo" tag v1.0.0
empty_output="$empty_repo/generated.md"
(cd "$empty_repo" && bash "$script_dir/changelog.sh" --output generated.md)
[[ "$(grep -c '^- None$' "$empty_output")" -eq 4 ]] || fail 'empty range did not emit four None entries'

# Failure modes: invalid refs, unknown options, and non-repository execution.
assert_fails 'invalid ref' bash -c "cd -- \"$tagged_repo\" && bash \"$script_dir/changelog.sh\" --since missing-ref"
assert_fails 'unknown option' bash "$script_dir/changelog.sh" --not-an-option
nonrepo="$tmp_dir/not-a-repo"
mkdir -p "$nonrepo"
assert_fails 'outside Git worktree' bash -c "cd -- \"$nonrepo\" && bash \"$script_dir/changelog.sh\""

echo 'test_changelog_deep.sh: PASS (range, categorization, remotes, output paths, empty history, and failures)'
