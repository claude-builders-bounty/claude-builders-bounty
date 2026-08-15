#!/usr/bin/env bash
# ==============================================================================
# tests/test_changelog.sh — Comprehensive test suite for changelog generator
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHANGELOG_SCRIPT="$SCRIPT_DIR/changelog.sh"

TEST_PASSED=0
TEST_FAILED=0

assert_contains() {
  local file="$1"
  local pattern="$2"
  local test_name="$3"

  if grep -qE "$pattern" "$file"; then
    echo "  [PASS] $test_name"
    TEST_PASSED=$((TEST_PASSED + 1))
  else
    echo "  [FAIL] $test_name (Pattern '$pattern' not found in $file)"
    echo "--- File Content ---"
    cat "$file"
    echo "--------------------"
    TEST_FAILED=$((TEST_FAILED + 1))
  fi
}

assert_not_contains() {
  local file="$1"
  local pattern="$2"
  local test_name="$3"

  if ! grep -qE "$pattern" "$file"; then
    echo "  [PASS] $test_name"
    TEST_PASSED=$((TEST_PASSED + 1))
  else
    echo "  [FAIL] $test_name (Pattern '$pattern' unexpectedly found in $file)"
    TEST_FAILED=$((TEST_FAILED + 1))
  fi
}

echo "=========================================="
echo "Running changelog.sh Test Suite"
echo "=========================================="

# Create temporary fixture repository
FIXTURE_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'changelog_fixture')
trap 'rm -rf "$FIXTURE_DIR"' EXIT

cd "$FIXTURE_DIR"
git init -q -b main
git config user.name "Test Bot"
git config user.email "bot@example.com"

# ------------------------------------------------------------------------------
# Test 1: Non-git directory fails gracefully
# ------------------------------------------------------------------------------
echo "Test 1: Non-git directory validation"
NON_GIT_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'non_git')
(
  cd "$NON_GIT_DIR"
  if ! bash "$CHANGELOG_SCRIPT" 2>/dev/null; then
    echo "  [PASS] Non-git directory exits with non-zero error"
    TEST_PASSED=$((TEST_PASSED + 1))
  else
    echo "  [FAIL] Non-git directory should have exited with error"
    TEST_FAILED=$((TEST_FAILED + 1))
  fi
)
rm -rf "$NON_GIT_DIR"

# ------------------------------------------------------------------------------
# Test 2: Categorization from initial repo without tags
# ------------------------------------------------------------------------------
echo "Test 2: Categorization of initial commits without tags"

echo "init" > file1.txt && git add file1.txt && git commit -q -m "feat(core): add user authentication system"
echo "fix" > file2.txt && git add file2.txt && git commit -q -m "fix(auth): resolve session timeout bug"
echo "doc" > file3.txt && git add file3.txt && git commit -q -m "docs: update API documentation"
echo "perf" > file4.txt && git add file4.txt && git commit -q -m "perf(db): optimize database index queries"
echo "del" > file5.txt && git add file5.txt && git commit -q -m "remove: remove deprecated legacy endpoints"

# Run generator
bash "$CHANGELOG_SCRIPT" --output CHANGELOG.md

assert_contains "CHANGELOG.md" "^# Changelog" "Header exists"
assert_contains "CHANGELOG.md" "^## \[Unreleased\]" "Release section exists"
assert_contains "CHANGELOG.md" "### Added" "Added category exists"
assert_contains "CHANGELOG.md" "add user authentication system" "Feat commit categorized in Added"
assert_contains "CHANGELOG.md" "### Fixed" "Fixed category exists"
assert_contains "CHANGELOG.md" "resolve session timeout bug" "Fix commit categorized in Fixed"
assert_contains "CHANGELOG.md" "### Changed" "Changed category exists"
assert_contains "CHANGELOG.md" "optimize database index queries" "Perf commit categorized in Changed"
assert_contains "CHANGELOG.md" "update API documentation" "Docs commit categorized in Changed"
assert_contains "CHANGELOG.md" "### Removed" "Removed category exists"
assert_contains "CHANGELOG.md" "remove deprecated legacy endpoints" "Remove commit categorized in Removed"

# ------------------------------------------------------------------------------
# Test 3: Tagged releases and git describe tag filtering
# ------------------------------------------------------------------------------
echo "Test 3: Tagged release and incremental changes since last tag"

git tag -a "v1.0.0" -m "Release v1.0.0"

# New commits after v1.0.0
echo "v1.1 feature" > feature.txt && git add feature.txt && git commit -q -m "feat(billing): integrate Stripe checkout portal"
echo "v1.1 fix" > bugfix.txt && git add bugfix.txt && git commit -q -m "fix(webhook): handle missing signature header"

# Merge commit simulation
git checkout -q -b feature-branch
echo "branch work" > branch.txt && git add branch.txt && git commit -q -m "chore(internal): cleanup scratch assets"
git checkout -q main
git merge -q --no-ff feature-branch -m "Merge branch 'feature-branch' into main"

bash "$CHANGELOG_SCRIPT" --version "v1.1.0" --output CHANGELOG.md

assert_contains "CHANGELOG.md" "## \[v1.1.0\]" "Release title updated to v1.1.0"
assert_contains "CHANGELOG.md" "integrate Stripe checkout portal" "New feature since v1.0.0 included"
assert_contains "CHANGELOG.md" "handle missing signature header" "New fix since v1.0.0 included"
assert_not_contains "CHANGELOG.md" "Merge branch" "Merge commits are excluded from changelog items"

# ------------------------------------------------------------------------------
# Test 4: Breaking change detection
# ------------------------------------------------------------------------------
echo "Test 4: Breaking change categorization"

git tag -a "v1.1.0" -m "Release v1.1.0"

echo "breaking 1" > break1.txt && git add break1.txt && git commit -q -m "feat!: switch to GraphQL API only"
echo "breaking 2" > break2.txt && git add break2.txt && git commit -q -m "refactor(config): overhaul environment variables" -m "BREAKING CHANGE: old config keys are removed"

bash "$CHANGELOG_SCRIPT" --version "v2.0.0" --output CHANGELOG.md

assert_contains "CHANGELOG.md" "## \[v2.0.0\]" "Major release header v2.0.0"
assert_contains "CHANGELOG.md" "### ⚠️ Breaking Changes" "Breaking changes header present"
assert_contains "CHANGELOG.md" "\*\*BREAKING\*\*: switch to GraphQL API only" "Breaking change with exclamation mark detected"
assert_contains "CHANGELOG.md" "\*\*BREAKING\*\*: overhaul environment variables" "Breaking change with footer detected"

# ------------------------------------------------------------------------------
# Test Summary
# ------------------------------------------------------------------------------
echo "=========================================="
echo "Test Results: ${TEST_PASSED} passed, ${TEST_FAILED} failed."
echo "=========================================="

if [[ "$TEST_FAILED" -gt 0 ]]; then
  exit 1
fi
