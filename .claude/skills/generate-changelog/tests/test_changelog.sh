#!/usr/bin/env bash
# Test suite for changelog.sh. Creates disposable temporary git repositories
# (never touches the developer's global git config or real repos) and
# exercises every required scenario for the /generate-changelog bounty.
#
# Usage: bash tests/test_changelog.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANGELOG_SH="${SCRIPT_DIR}/../changelog.sh"

PASS_COUNT=0
FAIL_COUNT=0
CURRENT_TEST=""

ROOT_TMP="$(mktemp -d "${TMPDIR:-/tmp}/changelog-tests.XXXXXX")"
cleanup() { rm -rf "$ROOT_TMP"; }
trap cleanup EXIT

start_test() {
  CURRENT_TEST="$1"
  echo ""
  echo "== ${CURRENT_TEST} =="
}

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "  PASS: $1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "  FAIL: $1"
}

assert_contains() {
  # assert_contains <file> <literal-substring> <message>
  if grep -qF -- "$2" "$1" 2>/dev/null; then
    pass "$3"
  else
    fail "$3 (did not find: $2)"
  fi
}

assert_not_contains() {
  if grep -qF -- "$2" "$1" 2>/dev/null; then
    fail "$3 (unexpectedly found: $2)"
  else
    pass "$3"
  fi
}

assert_file_missing() {
  if [ -f "$1" ]; then
    fail "$2 (file unexpectedly exists: $1)"
  else
    pass "$2"
  fi
}

assert_eq() {
  if [ "$1" = "$2" ]; then
    pass "$3"
  else
    fail "$3 (expected [$2], got [$1])"
  fi
}

# new_repo <name> -> prints path to a fresh, isolated git repo with local
# (never global) identity configured.
new_repo() {
  local dir="${ROOT_TMP}/$1"
  mkdir -p "$dir"
  ( cd "$dir" && git init -q && \
    git config user.name "Test User" && \
    git config user.email "test@example.com" && \
    git config commit.gpgsign false )
  echo "$dir"
}

commit_in() {
  # commit_in <repo> <message> [<filename>] — appends a unique line so each
  # commit actually changes tree content, without relying on GNU-only
  # `date +%N` (unsupported on BSD/macOS date).
  local repo="$1" msg="$2" fname="${3:-file.txt}"
  ( cd "$repo" && \
    printf 'change-%s-%s\n' "$RANDOM" "$RANDOM" >> "$fname" && \
    git add "$fname" && git commit -q -m "$msg" )
}

run_changelog() {
  # run_changelog <repo> -> runs script with cwd set to repo, captures stdout+stderr and exit code
  local repo="$1"
  ( cd "$repo" && bash "$CHANGELOG_SH" ) > "${repo}/.changelog_stdout" 2>&1
  echo $?
}

# ---------------------------------------------------------------------------
start_test "1: tagged repository + new commits after tag"
REPO="$(new_repo repo1)"
commit_in "$REPO" "Initial commit"
( cd "$REPO" && git tag v1.0.0 )
commit_in "$REPO" "feat: add new widget"
RC="$(run_changelog "$REPO")"
assert_eq "$RC" "0" "exits successfully"
assert_contains "${REPO}/CHANGELOG.md" "### Added" "has Added section"
assert_contains "${REPO}/CHANGELOG.md" "Add new widget" "contains the new commit"
assert_contains "${REPO}/.changelog_stdout" "v1.0.0..HEAD" "reports the analyzed range"

# ---------------------------------------------------------------------------
start_test "2: repository with no tags"
REPO="$(new_repo repo2)"
commit_in "$REPO" "feat: bootstrap project"
RC="$(run_changelog "$REPO")"
assert_eq "$RC" "0" "exits successfully"
assert_contains "${REPO}/.changelog_stdout" "No tags found" "reports no-tag fallback"
assert_contains "${REPO}/CHANGELOG.md" "Bootstrap project" "still generates a changelog"

# ---------------------------------------------------------------------------
start_test "3+4: feat: and feat(scope): map to Added"
REPO="$(new_repo repo3)"
commit_in "$REPO" "chore: init" a.txt
commit_in "$REPO" "feat: add login page" b.txt
commit_in "$REPO" "feat(api): add rate limiting" c.txt
run_changelog "$REPO" >/dev/null
assert_contains "${REPO}/CHANGELOG.md" "Add login page" "feat: -> Added"
assert_contains "${REPO}/CHANGELOG.md" "Add rate limiting" "feat(scope): -> Added"

# ---------------------------------------------------------------------------
start_test "5+6: fix: and fix(scope): map to Fixed"
REPO="$(new_repo repo4)"
commit_in "$REPO" "chore: init" a.txt
commit_in "$REPO" "fix: handle null pointer" b.txt
commit_in "$REPO" "fix(parser): handle empty input" c.txt
run_changelog "$REPO" >/dev/null
assert_contains "${REPO}/CHANGELOG.md" "### Fixed" "has Fixed section"
assert_contains "${REPO}/CHANGELOG.md" "Handle null pointer" "fix: -> Fixed"
assert_contains "${REPO}/CHANGELOG.md" "Handle empty input" "fix(scope): -> Fixed"

# ---------------------------------------------------------------------------
start_test "7: remove/delete map to Removed"
REPO="$(new_repo repo5)"
commit_in "$REPO" "chore: init" a.txt
commit_in "$REPO" "remove: legacy endpoint" b.txt
commit_in "$REPO" "deleted: unused config flag" c.txt
run_changelog "$REPO" >/dev/null
assert_contains "${REPO}/CHANGELOG.md" "### Removed" "has Removed section"
assert_contains "${REPO}/CHANGELOG.md" "Legacy endpoint" "remove: -> Removed"
assert_contains "${REPO}/CHANGELOG.md" "Unused config flag" "deleted: -> Removed"

# ---------------------------------------------------------------------------
start_test "8: refactor / unrecognized meaningful commit falls back to Changed"
REPO="$(new_repo repo6)"
commit_in "$REPO" "chore: init" a.txt
commit_in "$REPO" "refactor(core): simplify state machine" b.txt
commit_in "$REPO" "Improve internal docs generation" c.txt
run_changelog "$REPO" >/dev/null
assert_contains "${REPO}/CHANGELOG.md" "### Changed" "has Changed section"
assert_contains "${REPO}/CHANGELOG.md" "Simplify state machine" "refactor: -> Changed"
assert_contains "${REPO}/CHANGELOG.md" "Improve internal docs generation" "non-conventional commit preserved under Changed"

# ---------------------------------------------------------------------------
start_test "9: existing changelog release history is preserved"
REPO="$(new_repo repo7)"
cat > "${REPO}/CHANGELOG.md" <<'EOF'
# Changelog

## 2.0.0 - 2025-06-01

### Added
- Historic feature that must survive
EOF
commit_in "$REPO" "Initial commit"
( cd "$REPO" && git tag v2.0.0 )
commit_in "$REPO" "feat: add new thing"
run_changelog "$REPO" >/dev/null
assert_contains "${REPO}/CHANGELOG.md" "## 2.0.0 - 2025-06-01" "old release heading preserved"
assert_contains "${REPO}/CHANGELOG.md" "Historic feature that must survive" "old release content preserved"
assert_contains "${REPO}/CHANGELOG.md" "Add new thing" "new Unreleased entry also present"

# ---------------------------------------------------------------------------
start_test "10: running twice does not duplicate output"
REPO="$(new_repo repo8)"
commit_in "$REPO" "Initial commit"
( cd "$REPO" && git tag v1.0.0 )
commit_in "$REPO" "feat: add dashboard"
run_changelog "$REPO" >/dev/null
cp "${REPO}/CHANGELOG.md" "${REPO}/run1.md"
run_changelog "$REPO" >/dev/null
cp "${REPO}/CHANGELOG.md" "${REPO}/run2.md"
if diff -q "${REPO}/run1.md" "${REPO}/run2.md" >/dev/null 2>&1; then
  pass "output identical across repeated runs"
else
  fail "output differs between run1 and run2"
fi
OCCURRENCES="$(grep -c "Add dashboard" "${REPO}/CHANGELOG.md")"
assert_eq "$OCCURRENCES" "1" "entry appears exactly once (no duplication)"

# ---------------------------------------------------------------------------
start_test "11: zero commits since latest tag"
REPO="$(new_repo repo9)"
commit_in "$REPO" "feat: only commit"
( cd "$REPO" && git tag v1.0.0 )
RC="$(run_changelog "$REPO")"
assert_eq "$RC" "0" "exits successfully"
assert_contains "${REPO}/.changelog_stdout" "No commits found since v1.0.0" "reports no new commits"
assert_file_missing "${REPO}/CHANGELOG.md" "does not create CHANGELOG.md when there is nothing new"

# ---------------------------------------------------------------------------
start_test "12: punctuation in commit messages"
REPO="$(new_repo repo10)"
commit_in "$REPO" "chore: init" a.txt
commit_in "$REPO" "fix: handle it's \"weird\" edge-case; now works (mostly)" b.txt
run_changelog "$REPO" >/dev/null
assert_contains "${REPO}/CHANGELOG.md" "it's \"weird\" edge-case; now works (mostly)" "punctuation preserved verbatim"

# ---------------------------------------------------------------------------
start_test "13: issue references like #123 are preserved"
REPO="$(new_repo repo11)"
commit_in "$REPO" "chore: init" a.txt
commit_in "$REPO" "fix(auth): resolve session bug (#123)" b.txt
run_changelog "$REPO" >/dev/null
assert_contains "${REPO}/CHANGELOG.md" "#123" "issue reference preserved"

# ---------------------------------------------------------------------------
start_test "14: one-commit repository (no tags)"
REPO="$(new_repo repo12)"
commit_in "$REPO" "feat: initial release of the tool"
RC="$(run_changelog "$REPO")"
assert_eq "$RC" "0" "exits successfully"
assert_contains "${REPO}/CHANGELOG.md" "Initial release of the tool" "single commit categorized correctly"

# ---------------------------------------------------------------------------
start_test "15: merge commits are excluded by default"
REPO="$(new_repo repo13)"
commit_in "$REPO" "chore: init" a.txt
( cd "$REPO" && git checkout -q -b feature-branch )
commit_in "$REPO" "feat: branch-only feature" b.txt
( cd "$REPO" && if git checkout -q main 2>/dev/null; then :; else git checkout -q master; fi )
commit_in "$REPO" "fix: main branch fix" c.txt
( cd "$REPO" && git merge --no-ff -q -m "Merge branch 'feature-branch'" feature-branch )
run_changelog "$REPO" >/dev/null
assert_not_contains "${REPO}/CHANGELOG.md" "Merge branch" "merge commit subject excluded"
assert_contains "${REPO}/CHANGELOG.md" "Branch-only feature" "non-merge commit from merged branch still included"
assert_contains "${REPO}/CHANGELOG.md" "Main branch fix" "non-merge commit on main still included"

# ---------------------------------------------------------------------------
start_test "16: malicious-looking commit text is never executed"
REPO="$(new_repo repo14)"
CANARY="${REPO}/SHOULD_NOT_EXIST"
commit_in "$REPO" "chore: init" a.txt
commit_in "$REPO" "feat: add feature \$(touch ${CANARY})" b.txt
commit_in "$REPO" 'fix: handle `touch '"${CANARY}"'` in backticks' c.txt
commit_in "$REPO" "-rf --dangerous-looking-flag as a commit subject" d.txt
run_changelog "$REPO" >/dev/null
if [ -e "$CANARY" ]; then
  fail "command substitution in commit message was executed!"
else
  pass "command substitution in commit message stayed inert"
fi
assert_contains "${REPO}/CHANGELOG.md" '$(touch' "literal \$( ) text preserved in output"
assert_contains "${REPO}/CHANGELOG.md" '-rf --dangerous-looking-flag' "leading-dash commit subject preserved, not treated as a flag"

# ---------------------------------------------------------------------------
start_test "17: empty/whitespace-only commit subject never produces a bare bullet"
REPO="$(new_repo repo16)"
commit_in "$REPO" "chore: init" a.txt
( cd "$REPO" && printf 'x\n' >> b.txt && git add b.txt && git commit -q --allow-empty-message -m "" )
run_changelog "$REPO" >/dev/null
if grep -qE '^-[[:space:]]*$' "${REPO}/CHANGELOG.md"; then
  fail "found a bare/empty bullet in CHANGELOG.md"
else
  pass "no bare bullet emitted for empty commit subject"
fi
assert_contains "${REPO}/CHANGELOG.md" "Init" "the real commit is still present"

# ---------------------------------------------------------------------------
start_test "18: existing historical release internal formatting is preserved exactly"
REPO="$(new_repo repo17)"
cat > "${REPO}/CHANGELOG.md" <<'EOF'
# Changelog

## 2.0.0 - 2025-06-01

### Added

- First historical item


- Second historical item
EOF
# Capture the historical release block (from its heading to EOF) exactly as
# authored, including the intentional double blank line, before generation.
awk '/^## 2\.0\.0/{found=1} found{print}' "${REPO}/CHANGELOG.md" > "${REPO}/historical_before.txt"
commit_in "$REPO" "Initial commit"
( cd "$REPO" && git tag v2.0.0 )
commit_in "$REPO" "feat: add new thing"
run_changelog "$REPO" >/dev/null
awk '/^## 2\.0\.0/{found=1} found{print}' "${REPO}/CHANGELOG.md" > "${REPO}/historical_after.txt"
if diff -q "${REPO}/historical_before.txt" "${REPO}/historical_after.txt" >/dev/null 2>&1; then
  pass "historical release internal blank-line formatting preserved exactly"
else
  fail "historical release formatting was altered"
  diff "${REPO}/historical_before.txt" "${REPO}/historical_after.txt" || true
fi
assert_contains "${REPO}/CHANGELOG.md" "Add new thing" "new Unreleased entry still present alongside preserved history"

# ---------------------------------------------------------------------------
start_test "not a git repository"
NONGIT="${ROOT_TMP}/plain-dir"
mkdir -p "$NONGIT"
set +e
( cd "$NONGIT" && bash "$CHANGELOG_SH" ) > "${NONGIT}/out" 2>&1
RC=$?
set -e
if [ "$RC" -ne 0 ]; then pass "exits non-zero outside a git repo"; else fail "should exit non-zero outside a git repo"; fi
assert_file_missing "${NONGIT}/CHANGELOG.md" "does not create CHANGELOG.md outside a git repo"
assert_contains "${NONGIT}/out" "not inside a git repository" "prints a useful error"

# ---------------------------------------------------------------------------
start_test "repository with zero commits (unborn HEAD)"
REPO="$(new_repo repo15)"
RC="$(run_changelog "$REPO")"
assert_eq "$RC" "0" "exits successfully with no commits at all"
assert_file_missing "${REPO}/CHANGELOG.md" "does not create CHANGELOG.md when there are no commits"

# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo "Passed: ${PASS_COUNT}  Failed: ${FAIL_COUNT}"
echo "============================================"

if [ "$FAIL_COUNT" -ne 0 ]; then
  exit 1
fi
exit 0
