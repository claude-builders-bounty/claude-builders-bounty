#!/usr/bin/env bash
# Regression tests for changelog.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANGELOG_SH="${SCRIPT_DIR}/../changelog.sh"
ROOT_CHANGELOG_SH="${SCRIPT_DIR}/../../../changelog.sh"
PASS=0
FAIL=0

assert_contains() {
  local file="$1"
  local needle="$2"
  local label="$3"
  if grep -Fq "$needle" "$file"; then
    PASS=$((PASS + 1))
  else
    echo "FAIL: ${label} — expected output to contain: ${needle}" >&2
    echo "--- actual output ---" >&2
    cat "$file" >&2
    FAIL=$((FAIL + 1))
  fi
}

assert_not_contains() {
  local file="$1"
  local needle="$2"
  local label="$3"
  if grep -Fq "$needle" "$file"; then
    echo "FAIL: ${label} — output should not contain: ${needle}" >&2
    FAIL=$((FAIL + 1))
  else
    PASS=$((PASS + 1))
  fi
}

setup_repo() {
  local dir="$1"
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" config user.email "test@example.com"
  git -C "$dir" config user.name "Test User"
}

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

# Test 1: categorize commits and format output
REPO1="${TMP_ROOT}/repo1"
setup_repo "$REPO1"
printf 'base\n' >"$REPO1/README"
git -C "$REPO1" add README
git -C "$REPO1" commit -qm "Initial commit"
git -C "$REPO1" tag v1.0.0

printf 'feature\n' >"$REPO1/feature.txt"
git -C "$REPO1" add feature.txt
git -C "$REPO1" commit -qm "feat: add user login"

printf 'fix\n' >"$REPO1/fix.txt"
git -C "$REPO1" add fix.txt
git -C "$REPO1" commit -qm "fix: resolve null pointer crash"

printf 'change\n' >"$REPO1/change.txt"
git -C "$REPO1" add change.txt
git -C "$REPO1" commit -qm "refactor: simplify auth flow"

printf 'remove\n' >"$REPO1/remove.txt"
git -C "$REPO1" add remove.txt
git -C "$REPO1" commit -qm "remove: drop legacy API"

OUT1="${TMP_ROOT}/changelog1.md"
bash "$CHANGELOG_SH" "$REPO1" --output "$OUT1" >/dev/null

assert_contains "$OUT1" "# Changelog" "header"
assert_contains "$OUT1" "## [v1.0.0-next]" "version since tag"
assert_contains "$OUT1" "### Added" "added section"
assert_contains "$OUT1" "### Fixed" "fixed section"
assert_contains "$OUT1" "### Changed" "changed section"
assert_contains "$OUT1" "### Removed" "removed section"
assert_contains "$OUT1" "add user login" "feat message cleaned"
assert_contains "$OUT1" "resolve null pointer crash" "fix message cleaned"
assert_contains "$OUT1" "simplify auth flow" "refactor message cleaned"
assert_contains "$OUT1" "drop legacy API" "remove message cleaned"
assert_not_contains "$OUT1" "Initial commit" "pre-tag commit excluded"

# Test 2: scoped conventional commits
REPO1B="${TMP_ROOT}/repo1b"
setup_repo "$REPO1B"
printf 'base\n' >"$REPO1B/README"
git -C "$REPO1B" add README
git -C "$REPO1B" commit -qm "Initial commit"
git -C "$REPO1B" tag v1.0.0
printf 'feature\n' >"$REPO1B/feature.txt"
git -C "$REPO1B" add feature.txt
git -C "$REPO1B" commit -qm "feat(api): add scoped endpoint"

OUT1B="${TMP_ROOT}/changelog1b.md"
bash "$CHANGELOG_SH" "$REPO1B" --output "$OUT1B" >/dev/null

assert_contains "$OUT1B" "### Added" "scoped feat section"
assert_contains "$OUT1B" "add scoped endpoint" "scoped feat message cleaned"

# Test 3: no tags uses full history
REPO2="${TMP_ROOT}/repo2"
setup_repo "$REPO2"
printf 'one\n' >"$REPO2/a"
git -C "$REPO2" add a
git -C "$REPO2" commit -qm "feat: first feature"

OUT2="${TMP_ROOT}/changelog2.md"
bash "$CHANGELOG_SH" "$REPO2" --output "$OUT2" >/dev/null

assert_contains "$OUT2" "## [Unreleased]" "unreleased when no tags"
assert_contains "$OUT2" "first feature" "full history included"

# Test 4: --since overrides latest tag
REPO3="${TMP_ROOT}/repo3"
setup_repo "$REPO3"
printf 'base\n' >"$REPO3/README"
git -C "$REPO3" add README
git -C "$REPO3" commit -qm "Initial commit"
printf 'a\n' >"$REPO3/a"
git -C "$REPO3" add a
git -C "$REPO3" commit -qm "feat: between tags"
git -C "$REPO3" tag v2.0.0

printf 'b\n' >"$REPO3/b"
git -C "$REPO3" add b
git -C "$REPO3" commit -qm "fix: after v2"

OUT3="${TMP_ROOT}/changelog3.md"
bash "$CHANGELOG_SH" "$REPO3" --since v2.0.0 --output "$OUT3" >/dev/null

assert_contains "$OUT3" "after v2" "since tag includes later commits"
assert_not_contains "$OUT3" "between tags" "since tag excludes earlier commits"

# Test 5: --preview writes to stdout only
REPO4="${TMP_ROOT}/repo4"
setup_repo "$REPO4"
printf 'base\n' >"$REPO4/README"
git -C "$REPO4" add README
git -C "$REPO4" commit -qm "Initial commit"
git -C "$REPO4" tag v1.0.0
printf 'feature\n' >"$REPO4/feature.txt"
git -C "$REPO4" add feature.txt
git -C "$REPO4" commit -qm "feat: preview mode"

PREVIEW_OUT="${TMP_ROOT}/preview.txt"
bash "$CHANGELOG_SH" "$REPO4" --preview >"$PREVIEW_OUT" 2>/dev/null

assert_contains "$PREVIEW_OUT" "### Added" "preview mode added section"
assert_contains "$PREVIEW_OUT" "preview mode" "preview mode commit"
if [[ -f "$REPO4/CHANGELOG.md" ]]; then
  echo "FAIL: --preview should not write CHANGELOG.md" >&2
  FAIL=$((FAIL + 1))
else
  PASS=$((PASS + 1))
fi

# Test 6: --version overrides release header
REPO5="${TMP_ROOT}/repo5"
setup_repo "$REPO5"
printf 'base\n' >"$REPO5/README"
git -C "$REPO5" add README
git -C "$REPO5" commit -qm "Initial commit"
git -C "$REPO5" tag v2.0.0
printf 'feature\n' >"$REPO5/feature.txt"
git -C "$REPO5" add feature.txt
git -C "$REPO5" commit -qm "feat: version override"

OUT5="${TMP_ROOT}/changelog5.md"
bash "$CHANGELOG_SH" "$REPO5" --version 2.1.0 --output "$OUT5" >/dev/null
assert_contains "$OUT5" "## [2.1.0]" "custom version header"

# Test 7: repo-root changelog.sh wrapper delegates to the skill script
REPO6="${TMP_ROOT}/repo6"
setup_repo "$REPO6"
printf 'base\n' >"$REPO6/README"
git -C "$REPO6" add README
git -C "$REPO6" commit -qm "Initial commit"
git -C "$REPO6" tag v1.0.0
printf 'feature\n' >"$REPO6/feature.txt"
git -C "$REPO6" add feature.txt
git -C "$REPO6" commit -qm "feat: root wrapper"

OUT6="${TMP_ROOT}/changelog6.md"
bash "$ROOT_CHANGELOG_SH" "$REPO6" --output "$OUT6" >/dev/null
assert_contains "$OUT6" "### Added" "root wrapper produces Added section"
assert_contains "$OUT6" "root wrapper" "root wrapper categorizes feat commit"

# Test 8: non-git directory fails
set +e
bash "$CHANGELOG_SH" "$TMP_ROOT" --output "${TMP_ROOT}/bad.md" >/dev/null 2>&1
STATUS=$?
set -e
if [[ "$STATUS" -ne 0 ]]; then
  PASS=$((PASS + 1))
else
  echo "FAIL: non-git directory should exit non-zero" >&2
  FAIL=$((FAIL + 1))
fi

echo "Tests: ${PASS} passed, ${FAIL} failed"
[[ "$FAIL" -eq 0 ]]
