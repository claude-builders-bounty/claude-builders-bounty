#!/usr/bin/env bash
# ==============================================================================
# Automated Test Suite for changelog.sh
# Verifies commit categorization, Keep-a-Changelog formatting, and CLI flags
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="${SCRIPT_DIR}/changelog.sh"
TEST_REPO="$(mktemp -d /tmp/test-changelog-repo-XXXXXX)"

cleanup() {
  rm -rf "$TEST_REPO"
}
trap cleanup EXIT

echo "=== Initializing Mock Git Repository at ${TEST_REPO} ==="
cd "$TEST_REPO"
git init -b main
git config user.name "Test Runner"
git config user.email "test@example.com"

# Initial commit
echo "init" > README.md
git add README.md
git commit -m "chore: initial commit"
git tag v1.0.0

# Add categorized commits
echo "feature" > feat.txt
git add feat.txt
git commit -m "feat: implement interactive export modal"

echo "bugfix" > bug.txt
git add bug.txt
git commit -m "fix: resolve memory leak in connection pool"

echo "refactor" > refactor.txt
git add refactor.txt
git commit -m "refactor: simplify AST traversal pipeline"

echo "remove" > remove.txt
git add remove.txt
git commit -m "remove: deprecate legacy v1 authentication endpoints"

echo "=== Test 1: Run default changelog generation ==="
bash "$GENERATOR"

if [[ ! -f "CHANGELOG.md" ]]; then
  echo "FAIL: CHANGELOG.md was not generated." >&2
  exit 1
fi

CONTENT="$(cat CHANGELOG.md)"

echo "Checking content structure..."
assert_contains() {
  local pattern="$1"
  if ! echo "$CONTENT" | grep -F -q "$pattern"; then
    echo "FAIL: Expected output to contain '${pattern}'" >&2
    echo "Actual content:" >&2
    echo "$CONTENT" >&2
    exit 1
  fi
}

assert_contains "# Changelog"
assert_contains "## [Unreleased]"
assert_contains "### Added"
assert_contains "implement interactive export modal"
assert_contains "### Fixed"
assert_contains "resolve memory leak in connection pool"
assert_contains "### Changed"
assert_contains "simplify AST traversal pipeline"
assert_contains "### Removed"
assert_contains "deprecate legacy v1 authentication endpoints"

echo "✓ Test 1 passed: All 4 categories correctly parsed and formatted."

echo "=== Test 2: Custom version tag and dry-run flag ==="
DRY_RUN_OUTPUT="$(bash "$GENERATOR" --tag v1.1.0 --dry-run)"

if ! echo "$DRY_RUN_OUTPUT" | grep -q "## \[v1.1.0\]"; then
  echo "FAIL: Dry run output did not contain specified tag header." >&2
  exit 1
fi

echo "✓ Test 2 passed: Custom tag and dry-run flags working properly."

echo "=== Test 3: Custom output file ==="
bash "$GENERATOR" --output "CUSTOM_CHANGELOG.md" --tag v2.0.0

if [[ ! -f "CUSTOM_CHANGELOG.md" ]]; then
  echo "FAIL: Custom output file was not created." >&2
  exit 1
fi

if ! grep -q "## \[v2.0.0\]" "CUSTOM_CHANGELOG.md"; then
  echo "FAIL: Custom output file does not contain expected tag." >&2
  exit 1
fi

echo "✓ Test 3 passed: Custom output file flag functioning."

echo "=================================================="
echo "🎉 ALL TESTS PASSED SUCCESSFULLY (100% Green)"
echo "=================================================="
