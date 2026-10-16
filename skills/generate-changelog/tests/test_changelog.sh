#!/usr/bin/env bash
# ==============================================================================
# test_changelog.sh - Comprehensive automated unit test suite for changelog.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANGELOG_SH="${SCRIPT_DIR}/../changelog.sh"

PASSED=0
FAILED=0

assert_equals() {
  local expected="$1"
  local actual="$2"
  local msg="$3"
  if [ "$expected" = "$actual" ]; then
    echo "  [PASS] $msg"
    PASSED=$((PASSED + 1))
  else
    echo "  [FAIL] $msg (Expected: '$expected', Got: '$actual')"
    FAILED=$((FAILED + 1))
  fi
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="$3"
  if echo "$haystack" | grep -F -q "$needle"; then
    echo "  [PASS] $msg"
    PASSED=$((PASSED + 1))
  else
    echo "  [FAIL] $msg (Missing substring: '$needle')"
    FAILED=$((FAILED + 1))
  fi
}

echo "=== Running Changelog Generator Test Suite ==="

# Test 1: Help option returns exit code 0
OUT=$(bash "$CHANGELOG_SH" --help 2>&1)
CODE=$?
assert_equals 0 $CODE "Test 1: --help exits with code 0"
assert_contains "$OUT" "Usage: changelog.sh" "Test 1: --help contains usage info"

# Test 2: Unknown option returns exit code 2
set +e
OUT=$(bash "$CHANGELOG_SH" --invalid-flag 2>&1)
CODE=$?
set -e
assert_equals 2 $CODE "Test 2: Unknown flag exits with code 2"

# Test 3: Non-git directory returns exit code 4
TMP_NONGIT=$(mktemp -d)
set +e
OUT=$(bash "$CHANGELOG_SH" -C "$TMP_NONGIT" 2>&1)
CODE=$?
set -e
rm -rf "$TMP_NONGIT"
assert_equals 4 $CODE "Test 3: Non-git directory exits with code 4"

# Create a clean fixture Git repo for subsequent functional tests
FIXTURE_REPO=$(mktemp -d)
trap 'rm -rf "$FIXTURE_REPO"' EXIT

git -C "$FIXTURE_REPO" init --quiet -b main
git -C "$FIXTURE_REPO" config user.email "test@example.com"
git -C "$FIXTURE_REPO" config user.name "Test Runner"

# Commit 1: Initial commit (no tags yet)
echo "init" > "$FIXTURE_REPO/file.txt"
git -C "$FIXTURE_REPO" add .
git -C "$FIXTURE_REPO" commit -m "chore: initial commit" --quiet

# Commit 2: Added feature
echo "feat1" >> "$FIXTURE_REPO/file.txt"
git -C "$FIXTURE_REPO" commit -am "feat(core): add authentication module" --quiet

# Commit 3: Fixed bug
echo "fix1" >> "$FIXTURE_REPO/file.txt"
git -C "$FIXTURE_REPO" commit -am "fix(auth): resolve token expiration issue" --quiet

# Commit 4: Keyword fallback
echo "add1" >> "$FIXTURE_REPO/file.txt"
git -C "$FIXTURE_REPO" commit -am "Implement user profile endpoints" --quiet

# Commit 5: Breaking change
echo "break1" >> "$FIXTURE_REPO/file.txt"
git -C "$FIXTURE_REPO" commit -am "feat(api)!: migrate to GraphQL v2" --quiet

# Commit 6: Removed feature
echo "rem1" >> "$FIXTURE_REPO/file.txt"
git -C "$FIXTURE_REPO" commit -am "remove: legacy REST v1 handlers" --quiet

# Test 4: Generates changelog across all commits when no tags exist
OUT=$(bash "$CHANGELOG_SH" -C "$FIXTURE_REPO" -o -)
CODE=$?
assert_equals 0 $CODE "Test 4: Generate from root (no tags) succeeds"
assert_contains "$OUT" "### Added" "Test 4: Contains Added section"
assert_contains "$OUT" "Add authentication module" "Test 4: Categorized feat -> Added"
assert_contains "$OUT" "Implement user profile endpoints" "Test 4: Categorized keyword -> Added"
assert_contains "$OUT" "### Fixed" "Test 4: Contains Fixed section"
assert_contains "$OUT" "Resolve token expiration issue" "Test 4: Categorized fix -> Fixed"
assert_contains "$OUT" "### Removed" "Test 4: Contains Removed section"
assert_contains "$OUT" "Legacy REST v1 handlers" "Test 4: Categorized remove -> Removed"
assert_contains "$OUT" "**BREAKING:**" "Test 4: Breaking marker recognized"

# Now create tag v1.0.0 at current commit
git -C "$FIXTURE_REPO" tag -a "v1.0.0" -m "Release v1.0.0"

# Test 5: Empty range after tag returns exit code 5
set +e
OUT=$(bash "$CHANGELOG_SH" -C "$FIXTURE_REPO" -o - 2>&1)
CODE=$?
set -e
assert_equals 5 $CODE "Test 5: No commits since tag exits with code 5"

# Add commit after tag v1.0.0
echo "feat2" >> "$FIXTURE_REPO/file.txt"
git -C "$FIXTURE_REPO" commit -am "feat(billing): add Stripe webhooks integration" --quiet

# Test 6: Fetches only commits since tag v1.0.0
OUT=$(bash "$CHANGELOG_SH" -C "$FIXTURE_REPO" -o -)
CODE=$?
assert_equals 0 $CODE "Test 6: Commits since tag succeeds"
assert_contains "$OUT" "Add Stripe webhooks integration" "Test 6: Post-tag commit included"
if echo "$OUT" | grep -q "authentication module"; then
  echo "  [FAIL] Test 6: Pre-tag commit should not be included"
  FAILED=$((FAILED + 1))
else
  echo "  [PASS] Test 6: Pre-tag commit correctly excluded"
  PASSED=$((PASSED + 1))
fi

# Test 7: Output file already exists without --force returns exit code 3
TARGET_MD="$FIXTURE_REPO/CHANGELOG.md"
touch "$TARGET_MD"
set +e
OUT=$(bash "$CHANGELOG_SH" -C "$FIXTURE_REPO" -o "$TARGET_MD" 2>&1)
CODE=$?
set -e
assert_equals 3 $CODE "Test 7: File already exists exits with code 3"

# Test 8: Output file with --force overwrites successfully
set +e
OUT=$(bash "$CHANGELOG_SH" -C "$FIXTURE_REPO" -o "$TARGET_MD" --force 2>&1)
CODE=$?
set -e
assert_equals 0 $CODE "Test 8: --force overwrites file successfully"
assert_contains "$(cat "$TARGET_MD")" "Add Stripe webhooks integration" "Test 8: File content properly written"

# Test 9: Merge commits are filtered out
git -C "$FIXTURE_REPO" checkout -b feature-branch --quiet
echo "branch" >> "$FIXTURE_REPO/file.txt"
git -C "$FIXTURE_REPO" commit -am "feat(sub): branch feature" --quiet
git -C "$FIXTURE_REPO" checkout main --quiet
git -C "$FIXTURE_REPO" merge feature-branch --no-ff -m "Merge branch 'feature-branch'" --quiet

OUT=$(bash "$CHANGELOG_SH" -C "$FIXTURE_REPO" -o -)
if echo "$OUT" | grep -q "Merge branch"; then
  echo "  [FAIL] Test 9: Merge commit was not filtered"
  FAILED=$((FAILED + 1))
else
  echo "  [PASS] Test 9: Merge commits filtered out"
  PASSED=$((PASSED + 1))
fi

echo ""
echo "=== Test Summary ==="
echo "Total Passed: $PASSED"
echo "Total Failed: $FAILED"

if [ "$FAILED" -eq 0 ]; then
  echo "🎉 ALL TESTS PASSED (100%)"
  exit 0
else
  echo "❌ SOME TESTS FAILED"
  exit 1
fi
