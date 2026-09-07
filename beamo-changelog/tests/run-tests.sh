#!/usr/bin/env bash
# Unit + integration tests for beamo-changelog
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/changelog.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PASS=0
FAIL=0

assert_eq() {
  local name="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    echo "  PASS  $name"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $name"
    echo "        expected: $expected"
    echo "        actual:   $actual"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local name="$1" haystack="$2" needle="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  PASS  $name"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $name (missing: $needle)"
    FAIL=$((FAIL + 1))
  fi
}

assert_not_contains() {
  local name="$1" haystack="$2" needle="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    echo "  PASS  $name"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $name (unexpected: $needle)"
    FAIL=$((FAIL + 1))
  fi
}

# --- Source categorize via a tiny harness ---
# Extract categorize by running the script's functions in a subshell is hard;
# instead we validate via end-to-end fixture repos.

echo "== Fixture: conventional commits =="
REPO1="$TMP/repo-conv"
mkdir -p "$REPO1" && cd "$REPO1"
git init -q
git config user.email "test@example.com"
git config user.name "Test"
echo a > a.txt && git add a.txt && git commit -q -m "chore: initial"
git tag v0.1.0
echo b > b.txt && git add b.txt && git commit -q -m "feat: add widgets API"
echo c > c.txt && git add c.txt && git commit -q -m "fix: correct null pointer in parser"
echo d > d.txt && git add d.txt && git commit -q -m "refactor: simplify cache layer"
echo e > e.txt && git add e.txt && git commit -q -m "remove: drop legacy CLI flag"

OUT1="$("$SCRIPT" --repo "$REPO1" --stdout --replace)"
assert_contains "has Added section" "$OUT1" "### Added"
assert_contains "has Fixed section" "$OUT1" "### Fixed"
assert_contains "has Changed section" "$OUT1" "### Changed"
assert_contains "has Removed section" "$OUT1" "### Removed"
assert_contains "feat categorized Added" "$OUT1" "Add widgets API"
assert_contains "fix categorized Fixed" "$OUT1" "Correct null pointer"
assert_contains "refactor categorized Changed" "$OUT1" "Simplify cache layer"
assert_contains "remove categorized Removed" "$OUT1" "Drop legacy CLI flag"
assert_contains "Unreleased heading" "$OUT1" "## [Unreleased]"
assert_contains "since last tag range used" "$OUT1" "v0.1.0"

echo "== Fixture: keyword heuristics =="
REPO2="$TMP/repo-kw"
mkdir -p "$REPO2" && cd "$REPO2"
git init -q
git config user.email "test@example.com"
git config user.name "Test"
echo a > a.txt && git add a.txt && git commit -q -m "start"
git tag v1.0.0
echo b > b.txt && git add b.txt && git commit -q -m "Added dark mode toggle"
echo c > c.txt && git add c.txt && git commit -q -m "Fixed crash on empty input"
echo d > d.txt && git add d.txt && git commit -q -m "Updated dependencies"
echo e > e.txt && git add e.txt && git commit -q -m "Removed unused helper"

OUT2="$("$SCRIPT" --repo "$REPO2" --stdout)"
assert_contains "kw Added" "$OUT2" "### Added"
assert_contains "kw Fixed" "$OUT2" "### Fixed"
assert_contains "kw Changed" "$OUT2" "### Changed"
assert_contains "kw Removed" "$OUT2" "### Removed"
assert_contains "dark mode under Added" "$OUT2" "Added dark mode toggle"
assert_contains "crash under Fixed" "$OUT2" "Fixed crash on empty input"

echo "== Fixture: writes file =="
REPO3="$TMP/repo-write"
mkdir -p "$REPO3" && cd "$REPO3"
git init -q
git config user.email "test@example.com"
git config user.name "Test"
echo a > a.txt && git add a.txt && git commit -q -m "feat: hello"
"$SCRIPT" --repo "$REPO3" --replace -o "$REPO3/CHANGELOG.md" >/dev/null
assert_eq "file exists" "1" "$( [[ -f "$REPO3/CHANGELOG.md" ]] && echo 1 || echo 0 )"
assert_contains "file has changelog title" "$(cat "$REPO3/CHANGELOG.md")" "# Changelog"

echo "== Fixture: no commits since tag =="
REPO4="$TMP/repo-empty"
mkdir -p "$REPO4" && cd "$REPO4"
git init -q
git config user.email "test@example.com"
git config user.name "Test"
echo a > a.txt && git add a.txt && git commit -q -m "feat: only"
git tag v9.9.9
OUT4="$("$SCRIPT" --repo "$REPO4" --stdout)"
assert_contains "empty range message" "$OUT4" "No commits found"

echo "== Fixture: normal commands unaffected (script exits 0) =="
assert_eq "version flag" "0" "$( "$SCRIPT" -v >/dev/null && echo 0 || echo 1 )"
assert_eq "help flag" "0" "$( "$SCRIPT" -h >/dev/null && echo 0 || echo 1 )"

echo
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
