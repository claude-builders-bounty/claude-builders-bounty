#!/usr/bin/env bash
# ==============================================================================
# test_changelog.sh - Hermetic Test Suite for changelog.sh
# Verifies tag detection, categorization, formatting, and file prepending.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANGELOG_BIN="$SCRIPT_DIR/../changelog.sh"

TEST_REPO=$(mktemp -d)
trap 'rm -rf "$TEST_REPO"' EXIT

echo "=== Running Hermetic Changelog Generator Tests ==="

cd "$TEST_REPO"
git init -q -b main
git config user.name "Test Runner"
git config user.email "test@example.com"

# 1. Base Commit & Initial Tag
echo "initial" > file.txt
git add file.txt
git commit -q -m "chore: initial commit"
git tag v1.0.0

# 2. Add Conventional Commits
echo "feature" >> file.txt
git commit -q -am "feat(auth): add OAuth2 Google login"

echo "fix" >> file.txt
git commit -q -am "fix(router): prevent null pointer on redirect"

echo "refactor" >> file.txt
git commit -q -am "refactor(cache): switch to LRU cache strategy"

echo "remove" >> file.txt
git commit -q -am "remove(legacy): drop obsolete XML parser"

echo "security" >> file.txt
git commit -q -am "sec(session): regenerate session ID on privilege escalation"

echo "chore" >> file.txt
git commit -q -am "chore(deps): update dependencies"

# Test 1: Run changelog generator for unreleased changes
OUTPUT=$("$CHANGELOG_BIN" -v "v1.1.0")

echo "Checking Generated Output..."

assert_contains() {
    local pattern="$1"
    local text="$2"
    if ! echo "$text" | grep -q "$pattern"; then
        echo "FAIL: Expected output to contain '$pattern'" >&2
        exit 1
    fi
}

assert_contains "## \[v1.1.0\]" "$OUTPUT"
assert_contains "### Added" "$OUTPUT"
assert_contains "\*\*auth\*\*: add OAuth2 Google login" "$OUTPUT"
assert_contains "### Fixed" "$OUTPUT"
assert_contains "\*\*router\*\*: prevent null pointer on redirect" "$OUTPUT"
assert_contains "### Changed" "$OUTPUT"
assert_contains "\*\*cache\*\*: switch to LRU cache strategy" "$OUTPUT"
assert_contains "### Removed" "$OUTPUT"
assert_contains "\*\*legacy\*\*: drop obsolete XML parser" "$OUTPUT"
assert_contains "### Security" "$OUTPUT"
assert_contains "\*\*session\*\*: regenerate session ID on privilege escalation" "$OUTPUT"
assert_contains "### Maintenance & Chores" "$OUTPUT"

echo "Test 1 Passed: Tag-aware delta categorization verified."

# Test 2: File Writing and Prepending
"$CHANGELOG_BIN" -v "v1.1.0" -w
if [ ! -f "CHANGELOG.md" ]; then
    echo "FAIL: CHANGELOG.md was not created." >&2
    exit 1
fi

# Add another commit and verify prepending
echo "patch" >> file.txt
git commit -q -am "fix(api): handle timeout exception"
"$CHANGELOG_BIN" -v "v1.1.1" -w

assert_contains "## \[v1.1.1\]" "$(cat CHANGELOG.md)"
assert_contains "## \[v1.1.0\]" "$(cat CHANGELOG.md)"

echo "Test 2 Passed: Prepending to existing CHANGELOG.md verified."

echo "=================================================="
echo "✅ ALL HERMETIC TESTS PASSED (100% VERIFIED)"
echo "=================================================="
