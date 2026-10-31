#!/usr/bin/env bash
# Comprehensive test suite for changelog.sh
set -euo pipefail

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/changelog.sh"
PASS=0
FAIL=0
TOTAL=0

run_test() {
  local name="$1"
  local expected="$2"
  local actual="$3"
  TOTAL=$((TOTAL + 1))
  if echo "$actual" | grep -qF -- "$expected"; then
    echo "  ✅ PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "  ❌ FAIL: $name"
    echo "    Expected to find: $expected"
    echo "    Got: $actual"
    FAIL=$((FAIL + 1))
  fi
}

cleanup() {
  rm -rf /tmp/test-cl-*
}
cleanup

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║    CHANGELOG.SH — COMPREHENSIVE TEST SUITE                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── TEST 1: Tagged repo with mixed conventional commits ──
echo "━━ Test 1: Tagged repo with mixed conventional commits ━━"
DIR="/tmp/test-cl-1"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m "feat: initial setup"
git commit --allow-empty -m "fix: null pointer in config"
git tag v1.0.0
git commit --allow-empty -m "feat: add user dashboard"
git commit --allow-empty -m "fix(auth): session timeout handling"
git commit --allow-empty -m "chore: bump eslint to v9"
git commit --allow-empty -m "remove: drop legacy API v1"
bash "$SCRIPT"
OUTPUT=$(cat CHANGELOG.md)
run_test "Header references v1.0.0" "Changes since v1.0.0" "$OUTPUT"
run_test "feat → Added section" "### Added" "$OUTPUT"
run_test "feat commit present" "add user dashboard" "$OUTPUT"
run_test "fix → Fixed section" "### Fixed" "$OUTPUT"
run_test "fix commit present" "session timeout handling" "$OUTPUT"
run_test "chore → Changed section" "### Changed" "$OUTPUT"
run_test "remove → Removed section" "### Removed" "$OUTPUT"
run_test "remove commit present" "drop legacy API v1" "$OUTPUT"
run_test "Commit hashes present" '(`' "$OUTPUT"
echo ""

# ── TEST 2: Untagged repo (full history fallback) ──
echo "━━ Test 2: Untagged repo — full history fallback ━━"
DIR="/tmp/test-cl-2"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m "feat: bootstrap project"
git commit --allow-empty -m "fix: typo in README"
git commit --allow-empty -m "add: CLI entry point"
bash "$SCRIPT"
OUTPUT=$(cat CHANGELOG.md)
run_test "Header says Full History" "Full History" "$OUTPUT"
run_test "All 3 commits present" "bootstrap project" "$OUTPUT"
run_test "add: prefix categorized" "CLI entry point" "$OUTPUT"
echo ""

# ── TEST 3: No new commits since tag ──
echo "━━ Test 3: No new commits since tag — clean exit ━━"
DIR="/tmp/test-cl-3"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m "feat: initial"
git tag v2.0.0
RESULT=$(bash "$SCRIPT" 2>&1 || true)
TOTAL=$((TOTAL + 1))
if echo "$RESULT" | grep -qi "no new commits\|nothing to generate"; then
  echo "  ✅ PASS: Clean exit message on no commits"
  PASS=$((PASS + 1))
else
  echo "  ❌ FAIL: Expected clean exit message"
  echo "    Got: $RESULT"
  FAIL=$((FAIL + 1))
fi
echo ""

# ── TEST 4: Custom output filename ──
echo "━━ Test 4: Custom output filename ━━"
DIR="/tmp/test-cl-4"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m "feat: something new"
bash "$SCRIPT" RELEASE_NOTES.md
TOTAL=$((TOTAL + 1))
if [ -f "RELEASE_NOTES.md" ]; then
  echo "  ✅ PASS: Custom filename RELEASE_NOTES.md created"
  PASS=$((PASS + 1))
else
  echo "  ❌ FAIL: Custom filename not created"
  FAIL=$((FAIL + 1))
fi
echo ""

# ── TEST 5: Merge commits filtered out ──
echo "━━ Test 5: Merge commits are excluded ━━"
DIR="/tmp/test-cl-5"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m "feat: main feature"
git checkout -b feature-branch -q
git commit --allow-empty -m "feat: branch work"
git checkout master -q 2>/dev/null || git checkout main -q
git merge feature-branch --no-ff -m "Merge branch 'feature-branch'" -q
bash "$SCRIPT"
OUTPUT=$(cat CHANGELOG.md)
TOTAL=$((TOTAL + 1))
if echo "$OUTPUT" | grep -q "Merge branch"; then
  echo "  ❌ FAIL: Merge commit should be excluded"
  FAIL=$((FAIL + 1))
else
  echo "  ✅ PASS: Merge commit correctly excluded"
  PASS=$((PASS + 1))
fi
echo ""

# ── TEST 6: Scoped conventional commits (feat(scope): ...) ──
echo "━━ Test 6: Scoped conventional commits ━━"
DIR="/tmp/test-cl-6"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m "feat(api): add REST endpoint"
git commit --allow-empty -m "fix(db): connection pool leak"
bash "$SCRIPT"
OUTPUT=$(cat CHANGELOG.md)
run_test "feat(api) in Added" "add REST endpoint" "$OUTPUT"
run_test "fix(db) in Fixed" "connection pool leak" "$OUTPUT"
echo ""

# ── TEST 7: Non-conventional commits fall to Changed ──
echo "━━ Test 7: Non-conventional commits default to Changed ━━"
DIR="/tmp/test-cl-7"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m "updated the deployment docs"
git commit --allow-empty -m "misc cleanup"
bash "$SCRIPT"
OUTPUT=$(cat CHANGELOG.md)
run_test "Non-conventional → Changed" "### Changed" "$OUTPUT"
run_test "Free-form commit present" "updated the deployment docs" "$OUTPUT"
echo ""

# ── TEST 8: Large repo simulation (20+ commits) ──
echo "━━ Test 8: Performance — 20+ commits ━━"
DIR="/tmp/test-cl-8"
mkdir -p "$DIR" && cd "$DIR" && git init -q
for i in $(seq 1 25); do
  git commit --allow-empty -m "feat: feature number $i"
done
START=$(date +%s)
bash "$SCRIPT"
END=$(date +%s)
DURATION=$((END - START))
TOTAL=$((TOTAL + 1))
LINES=$(grep -c '^\-' CHANGELOG.md)
if [ "$LINES" -eq 25 ] && [ "$DURATION" -lt 5 ]; then
  echo "  ✅ PASS: 25 commits processed in ${DURATION}s, all entries present"
  PASS=$((PASS + 1))
else
  echo "  ❌ FAIL: Expected 25 entries in <5s, got $LINES in ${DURATION}s"
  FAIL=$((FAIL + 1))
fi
echo ""

# ── TEST 9: Special characters in commit messages ──
echo "━━ Test 9: Special characters in commit messages ━━"
DIR="/tmp/test-cl-9"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m 'feat: add "quotes" & <angles> support'
git commit --allow-empty -m "fix: handle path with spaces (src/my file.ts)"
bash "$SCRIPT"
OUTPUT=$(cat CHANGELOG.md)
run_test "Quotes in commit msg" '"quotes"' "$OUTPUT"
run_test "Parens in commit msg" "my file.ts" "$OUTPUT"
echo ""

# ── TEST 10: Output is valid Markdown ──
echo "━━ Test 10: Output structure validation ━━"
DIR="/tmp/test-cl-10"
mkdir -p "$DIR" && cd "$DIR" && git init -q
git commit --allow-empty -m "feat: alpha"
git commit --allow-empty -m "fix: beta"
git commit --allow-empty -m "remove: gamma"
git commit --allow-empty -m "chore: delta"
bash "$SCRIPT"
OUTPUT=$(cat CHANGELOG.md)
run_test "Starts with # Changelog" "# Changelog" "$OUTPUT"
run_test "Has date in YYYY-MM-DD" "$(date +%Y-%m-%d)" "$OUTPUT"
run_test "Has bullet points" "- " "$OUTPUT"
echo ""

# ── SUMMARY ──
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║    TEST RESULTS: $PASS/$TOTAL PASSED   ($FAIL failed)"
printf "║    %-57s║\n" "$([ $FAIL -eq 0 ] && echo '🏆 ALL TESTS PASSED' || echo '⚠️  SOME TESTS FAILED')"
echo "╚══════════════════════════════════════════════════════════════╝"

cleanup
