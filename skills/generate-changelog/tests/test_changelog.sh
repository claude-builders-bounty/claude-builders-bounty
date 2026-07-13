#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
GENERATOR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)/changelog.sh
tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/test-generate-changelog.XXXXXX")
trap 'rm -rf -- "$tmpdir"' EXIT HUP INT TERM
pass=0

fail() { printf 'not ok - %s\n' "$*" >&2; exit 1; }
assert_contains() { grep -Fq -- "$2" "$1" || fail "expected '$2' in $1"; }
assert_not_contains() { ! grep -Fq -- "$2" "$1" || fail "did not expect '$2' in $1"; }
ok() { pass=$((pass + 1)); printf 'ok %s - %s\n' "$pass" "$1"; }

repo="$tmpdir/repo with spaces"
git init -q "$repo"
git -C "$repo" config user.name 'Test User'
git -C "$repo" config user.email test@example.com
main_branch=$(git -C "$repo" symbolic-ref --short HEAD)

commit() {
  local message=$1 marker=$2
  printf '%s\n' "$marker" >>"$repo/history.txt"
  git -C "$repo" add history.txt
  git -C "$repo" commit -q -m "$message"
}

commit 'feat: before tag and must be excluded' before
git -C "$repo" tag v1.0.0
commit 'feat(api)!: add OAuth login' added
commit 'fix: repair redirect loop' fixed
commit 'docs: explain configuration' changed
commit 'remove: delete legacy endpoint' removed
commit 'A plain uncategorized subject' fallback

output="$tmpdir/output with spaces.md"
bash "$GENERATOR" --repo "$repo" --output "$output" --version vNext >/dev/null

assert_contains "$output" '## [vNext]'
assert_contains "$output" '### Added'
assert_contains "$output" '### Fixed'
assert_contains "$output" '### Changed'
assert_contains "$output" '### Removed'
assert_contains "$output" 'feat(api)!: add OAuth login'
assert_contains "$output" 'fix: repair redirect loop'
assert_contains "$output" 'docs: explain configuration'
assert_contains "$output" 'remove: delete legacy endpoint'
assert_contains "$output" 'A plain uncategorized subject'
assert_not_contains "$output" 'before tag and must be excluded'
assert_contains "$output" 'Generated from v1.0.0..HEAD; 5 commit(s).'
ok 'uses latest tag and emits all four categories'

git -C "$repo" checkout -q -b topic HEAD~1
printf 'topic\n' >"$repo/topic.txt"
git -C "$repo" add topic.txt
git -C "$repo" commit -q -m 'feat: topic work'
git -C "$repo" checkout -q "$main_branch"
git -C "$repo" merge -q --no-ff topic -m 'feat: merge subject must be excluded'
bash "$GENERATOR" --repo "$repo" --output "$output" --force >/dev/null
assert_not_contains "$output" 'merge subject must be excluded'
assert_contains "$output" 'feat: topic work'
ok 'excludes merge commits but keeps merged changes'

no_tags="$tmpdir/no-tags"
git init -q "$no_tags"
git -C "$no_tags" config user.name 'Test User'
git -C "$no_tags" config user.email test@example.com
printf 'x\n' >"$no_tags/file"
git -C "$no_tags" add file
git -C "$no_tags" commit -q -m 'Initial commit'
bash "$GENERATOR" --repo "$no_tags" --output "$output" --force >/dev/null
assert_contains "$output" 'Initial commit'
assert_contains "$output" 'Generated from repository start..HEAD; 1 commit(s).'
ok 'falls back to full history when no tag exists'

git -C "$no_tags" tag v0.1.0
bash "$GENERATOR" --repo "$no_tags" --output "$output" --force >/dev/null
assert_contains "$output" '_No changes._'
assert_contains "$output" 'Generated from v0.1.0..HEAD; 0 commit(s).'
ok 'handles a tag with no newer commits'

preview=$(bash "$GENERATOR" --repo "$repo" --since HEAD~1 --output -)
[[ "$preview" == '# Changelog'* ]] || fail 'stdout preview missing header'
[[ "$preview" == *'1 commit(s)'* ]] || fail 'explicit range did not select one non-merge commit'
ok 'supports explicit range and stdout preview'

if bash "$GENERATOR" --repo "$tmpdir" --output "$output" >/dev/null 2>&1; then
  fail 'non-git directory should fail'
fi
ok 'rejects non-git directories'

printf 'keep me\n' >"$output"
if bash "$GENERATOR" --repo "$repo" --output "$output" >/dev/null 2>&1; then
  fail 'existing output should require --force'
fi
assert_contains "$output" 'keep me'
ok 'preserves existing output unless force is explicit'

output_dir="$tmpdir/output-dir"
mkdir "$output_dir"
if bash "$GENERATOR" --repo "$repo" --output "$output_dir" --force >/dev/null 2>&1; then
  fail 'directory output should fail'
fi
ok 'rejects an output path that is a directory'

printf '1..%s\n' "$pass"
