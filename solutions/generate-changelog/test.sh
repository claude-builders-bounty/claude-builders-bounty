#!/usr/bin/env bash
set -euo pipefail

script="${CHANGELOG_SCRIPT:-$(cd "$(dirname "$0")" && pwd)/changelog.sh}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_AUTHOR_NAME='Changelog Test'
export GIT_AUTHOR_EMAIL='test@example.invalid'
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
passed=0

pass() { passed=$((passed + 1)); printf 'ok %s - %s\n' "$passed" "$1"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
init_repo() { git init -q "$1"; }
commit() { git -C "$repo" -c commit.gpgSign=false commit -q --allow-empty -m "$1"; }
run() { bash "$script" "$repo" > "$work/stdout" 2> "$work/stderr"; }
assert_category() {
  local category="$1" subject="$2"
  awk -v category="$category" -v subject="$subject" '
    /^### / { section = substr($0, 5) }
    index($0, "- " subject " (`") == 1 {
      count++
      if (section != category) wrong++
    }
    END { exit !(count == 1 && wrong == 0) }
  ' "$repo/CHANGELOG.md" || fail "Expected '$subject' exactly once in $category"
}
assert_failure() {
  if run; then fail 'Expected a nonzero exit status'; fi
  if grep -q '^Wrote ' "$work/stdout"; then fail 'Reported success after failure'; fi
}

repo="$work/classification repo"
init_repo "$repo"
commit 'chore: initial history'
git -C "$repo" tag v1.0.0
for subject in 'feat(api): export invoices' 'feat!: new API' 'FEAT(ui)!: new layout' 'feat: add dashboard' 'fix(parser): handle EOF' 'fix!: remove race' 'fix: duplicate upload' 'bugfix(io)!: repair writes' 'remove(api)!: old endpoint' 'delete(ui): legacy button' 'remove: legacy job' 'docs: clarify setup' 'refactor!: replace internals' 'feat(): invalid empty scope' 'feature: unknown type' 'Added a report' 'Fixed upload' 'Drop old endpoint'; do
  commit "$subject"
done
run
for subject in 'feat(api): export invoices' 'feat!: new API' 'FEAT(ui)!: new layout' 'feat: add dashboard'; do assert_category Added "$subject"; done
pass 'scoped, unscoped, breaking and case-insensitive features'
for subject in 'fix(parser): handle EOF' 'fix!: remove race' 'fix: duplicate upload' 'bugfix(io)!: repair writes'; do assert_category Fixed "$subject"; done
pass 'scoped, unscoped and breaking fixes'
for subject in 'remove(api)!: old endpoint' 'delete(ui): legacy button' 'remove: legacy job'; do assert_category Removed "$subject"; done
pass 'scoped, unscoped and breaking removals'
for subject in 'docs: clarify setup' 'refactor!: replace internals' 'feat(): invalid empty scope' 'feature: unknown type'; do assert_category Changed "$subject"; done
pass 'unknown and malformed prefixes fall back to Changed'
assert_category Added 'Added a report'
assert_category Fixed 'Fixed upload'
assert_category Removed 'Drop old endpoint'
pass 'readable verbs retain their categories'
grep -q '^## Changes since v1.0.0$' "$repo/CHANGELOG.md"
if grep -q 'initial history' "$repo/CHANGELOG.md"; then fail 'Included a commit before the tag'; fi
pass 'only includes commits after the latest reachable tag'
cp "$repo/CHANGELOG.md" "$work/expected"
run
cmp "$work/expected" "$repo/CHANGELOG.md"
pass 'repeated runs are identical and do not duplicate entries'
mkdir "$repo/subdirectory"
(cd "$repo/subdirectory" && bash "$script" > "$work/stdout")
cmp "$work/expected" "$repo/CHANGELOG.md"
test ! -e "$repo/subdirectory/CHANGELOG.md"
pass 'default path from a subdirectory writes to the repository root'

repo="$work/no-tags"
init_repo "$repo"
commit 'feat: first commit'
run
grep -q '^## Changes (no previous tag)$' "$repo/CHANGELOG.md"
assert_category Added 'feat: first commit'
pass 'repositories without tags include all history'
git -C "$repo" tag v2.0.0
run
test "$(grep -c '^_No changes._$' "$repo/CHANGELOG.md")" -eq 4
pass 'tag at HEAD produces four empty sections successfully'

repo="$work/empty"
init_repo "$repo"
assert_failure
test ! -e "$repo/CHANGELOG.md"
grep -q 'has no commits' "$work/stderr"
pass 'empty repositories fail without creating a changelog'
printf 'Keep existing notes.\n' > "$repo/CHANGELOG.md"
cp "$repo/CHANGELOG.md" "$work/expected"
assert_failure
cmp "$work/expected" "$repo/CHANGELOG.md"
pass 'empty repositories preserve an existing changelog'

repo="$work/not-a-repository"
mkdir "$repo"
assert_failure
test ! -e "$repo/CHANGELOG.md"
pass 'non-repositories fail without creating output'
repo="$work/bare.git"
git init -q --bare "$repo"
assert_failure
test ! -e "$repo/CHANGELOG.md"
pass 'bare repositories fail clearly'

repo="$work/log-failure"
init_repo "$repo"
commit 'feat: initial commit'
printf 'Keep existing notes.\n' > "$repo/CHANGELOG.md"
cp "$repo/CHANGELOG.md" "$work/expected"
real_git="$(command -v git)"
mkdir "$work/bin"
cat > "$work/bin/git" <<'WRAPPER'
#!/usr/bin/env bash
if [[ "${3:-}" == log ]]; then
  printf 'fatal: simulated history read failure\n' >&2
  exit 128
fi
exec "$REAL_GIT" "$@"
WRAPPER
chmod +x "$work/bin/git"
export REAL_GIT="$real_git"
PATH="$work/bin:$PATH" assert_failure
cmp "$work/expected" "$repo/CHANGELOG.md"
grep -q 'could not read git history' "$work/stderr"
pass 'git log failures return an error and preserve existing output'

if find "$work" -name '.CHANGELOG.md.*' -print | grep -q .; then fail 'Temporary output was left behind'; fi
pass 'temporary output files are cleaned up'
printf 'All %s checks passed.\n' "$passed"
