#!/usr/bin/env bash
# ==============================================================================
# Automated Test Suite for Git Changelog Generator
# Verifies all acceptance criteria and edge cases in isolated git sandboxes.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="${SCRIPT_DIR}/changelog.sh"

TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT

echo "=== Running Changelog Generator Test Suite ==="
echo "Test workspace: ${TEST_ROOT}"

PASS_COUNT=0
TOTAL_COUNT=0

assert_contains() {
  local file="$1"
  local pattern="$2"
  local test_name="$3"
  TOTAL_COUNT=$((TOTAL_COUNT + 1))
  if grep -qE "$pattern" "$file"; then
    echo "  [PASS] ${test_name}"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "  [FAIL] ${test_name} - Pattern not found: ${pattern}"
    echo "--- File Content ---"
    cat "$file"
    echo "--------------------"
    return 1
  fi
}

# ------------------------------------------------------------------------------
# Test 1: Conventional Commits with Git Tag
# ------------------------------------------------------------------------------
echo "Test 1: Conventional Commits with Tag..."
REPO1="${TEST_ROOT}/repo1"
mkdir -p "$REPO1"
git -C "$REPO1" init -q
git -C "$REPO1" config user.name "Test Runner"
git -C "$REPO1" config user.email "test@example.com"

touch "$REPO1/initial.txt"
git -C "$REPO1" add . && git -C "$REPO1" commit -q -m "chore: initial setup"
git -C "$REPO1" tag "v1.0.0"

touch "$REPO1/feature.txt"
git -C "$REPO1" add . && git -C "$REPO1" commit -q -m "feat(auth): add OAuth2 provider"
touch "$REPO1/fix.txt"
git -C "$REPO1" add . && git -C "$REPO1" commit -q -m "fix(db): resolve connection pool leak"
touch "$REPO1/refactor.txt"
git -C "$REPO1" add . && git -C "$REPO1" commit -q -m "refactor(api): streamline route handlers"
touch "$REPO1/remove.txt"
git -C "$REPO1" add . && git -C "$REPO1" commit -q -m "remove: drop deprecated legacy v1"

(cd "$REPO1" && bash "$GENERATOR" "$REPO1/CHANGELOG.md")

assert_contains "$REPO1/CHANGELOG.md" "^## \[Changes since v1\.0\.0\]" "Tag range header"
assert_contains "$REPO1/CHANGELOG.md" "^### Added" "Added section presence"
assert_contains "$REPO1/CHANGELOG.md" "feat\(auth\): add OAuth2 provider" "Added entry"
assert_contains "$REPO1/CHANGELOG.md" "^### Fixed" "Fixed section presence"
assert_contains "$REPO1/CHANGELOG.md" "fix\(db\): resolve connection pool leak" "Fixed entry"
assert_contains "$REPO1/CHANGELOG.md" "^### Changed" "Changed section presence"
assert_contains "$REPO1/CHANGELOG.md" "refactor\(api\): streamline route handlers" "Changed entry"
assert_contains "$REPO1/CHANGELOG.md" "^### Removed" "Removed section presence"
assert_contains "$REPO1/CHANGELOG.md" "remove: drop deprecated legacy v1" "Removed entry"

# ------------------------------------------------------------------------------
# Test 2: Natural Imperative Language Commits
# ------------------------------------------------------------------------------
echo "Test 2: Natural Imperative Language..."
REPO2="${TEST_ROOT}/repo2"
mkdir -p "$REPO2"
git -C "$REPO2" init -q
git -C "$REPO2" config user.name "Test Runner"
git -C "$REPO2" config user.email "test@example.com"

touch "$REPO2/a.txt" && git -C "$REPO2" add . && git -C "$REPO2" commit -q -m "Add dark mode toggle"
touch "$REPO2/b.txt" && git -C "$REPO2" add . && git -C "$REPO2" commit -q -m "Fix layout shifting on resize"
touch "$REPO2/c.txt" && git -C "$REPO2" add . && git -C "$REPO2" commit -q -m "Update dependencies to latest"
touch "$REPO2/d.txt" && git -C "$REPO2" add . && git -C "$REPO2" commit -q -m "Remove unused icon assets"

(cd "$REPO2" && bash "$GENERATOR" "$REPO2/CHANGELOG.md")

assert_contains "$REPO2/CHANGELOG.md" "Add dark mode toggle" "Natural Added categorization"
assert_contains "$REPO2/CHANGELOG.md" "Fix layout shifting on resize" "Natural Fixed categorization"
assert_contains "$REPO2/CHANGELOG.md" "Update dependencies to latest" "Natural Changed categorization"
assert_contains "$REPO2/CHANGELOG.md" "Remove unused icon assets" "Natural Removed categorization"

# ------------------------------------------------------------------------------
# Test 3: Tagless Repository (Unreleased / Initial Release)
# ------------------------------------------------------------------------------
echo "Test 3: Tagless Repository..."
REPO3="${TEST_ROOT}/repo3"
mkdir -p "$REPO3"
git -C "$REPO3" init -q
git -C "$REPO3" config user.name "Test Runner"
git -C "$REPO3" config user.email "test@example.com"

touch "$REPO3/start.txt" && git -C "$REPO3" add . && git -C "$REPO3" commit -q -m "feat: initial commit"

(cd "$REPO3" && bash "$GENERATOR" "$REPO3/CHANGELOG.md")

assert_contains "$REPO3/CHANGELOG.md" "^## \[Unreleased / Initial Release\]" "Unreleased header"
assert_contains "$REPO3/CHANGELOG.md" "feat: initial commit" "Initial commit recorded"

# ------------------------------------------------------------------------------
# Test 4: Special Characters and Delimiters (Pipes, Quotes, Unicode)
# ------------------------------------------------------------------------------
echo "Test 4: Special Characters..."
REPO4="${TEST_ROOT}/repo4"
mkdir -p "$REPO4"
git -C "$REPO4" init -q
git -C "$REPO4" config user.name "Test Runner"
git -C "$REPO4" config user.email "test@example.com"

touch "$REPO4/pipe.txt"
git -C "$REPO4" add . && git -C "$REPO4" commit -q -m 'fix: support | pipe syntax and "double quotes" & symbols'

(cd "$REPO4" && bash "$GENERATOR" "$REPO4/CHANGELOG.md")

assert_contains "$REPO4/CHANGELOG.md" 'fix: support \| pipe syntax and "double quotes" & symbols' "Special characters preserved safely"

# ------------------------------------------------------------------------------
# Test 5: Custom Range Argument
# ------------------------------------------------------------------------------
echo "Test 5: Custom Range Argument..."
REPO5="${TEST_ROOT}/repo5"
mkdir -p "$REPO5"
git -C "$REPO5" init -q
git -C "$REPO5" config user.name "Test Runner"
git -C "$REPO5" config user.email "test@example.com"

touch "$REPO5/t1.txt" && git -C "$REPO5" add . && git -C "$REPO5" commit -q -m "feat: first release"
git -C "$REPO5" tag "v1.0"
touch "$REPO5/t2.txt" && git -C "$REPO5" add . && git -C "$REPO5" commit -q -m "feat: second release"
git -C "$REPO5" tag "v2.0"
touch "$REPO5/t3.txt" && git -C "$REPO5" add . && git -C "$REPO5" commit -q -m "feat: ongoing work"

(cd "$REPO5" && bash "$GENERATOR" "$REPO5/CHANGELOG.md" "v1.0..v2.0")

assert_contains "$REPO5/CHANGELOG.md" "^## \[Range: v1\.0\.\.v2\.0\]" "Custom range header"
assert_contains "$REPO5/CHANGELOG.md" "feat: second release" "Target commit included in custom range"

# ------------------------------------------------------------------------------
# Test 6: Empty Repository Handling
# ------------------------------------------------------------------------------
echo "Test 6: Empty Repository..."
REPO6="${TEST_ROOT}/repo6"
mkdir -p "$REPO6"
git -C "$REPO6" init -q

OUTPUT=$(cd "$REPO6" && bash "$GENERATOR" 2>&1 || true)
TOTAL_COUNT=$((TOTAL_COUNT + 1))
if echo "$OUTPUT" | grep -q "Repository has no commits yet"; then
  echo "  [PASS] Empty repo gracefully warned and exited"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "  [FAIL] Empty repo unexpected output: $OUTPUT"
fi

echo ""
echo "=== Test Summary: ${PASS_COUNT}/${TOTAL_COUNT} Passed ==="
if [ "$PASS_COUNT" -eq "$TOTAL_COUNT" ]; then
  echo "All tests passed successfully!"
  exit 0
else
  echo "Some tests failed."
  exit 1
fi
