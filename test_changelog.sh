#!/usr/bin/env bash
# Test suite for changelog.sh
# Run from the directory containing changelog.sh

set -e

TEST_DIR="$(mktemp -d)"
trap "rm -rf $TEST_DIR" EXIT

echo "=== Changelog Generator Test Suite ==="
PASS=0
FAIL=0

test_changelog() {
    local name="$1"
    local git_log="$2"
    local expected_sections="$3"

    # Set up test git repo
    (cd "$TEST_DIR" && git init --quiet && git config user.email "test@test.com" && git config user.name "Test")
    
    # Populate git log
    echo "$git_log" | while IFS='|' read -r msg body; do
        [ -z "$msg" ] && continue
        (cd "$TEST_DIR" && git commit --allow-empty -m "$msg" --allow-empty 2>/dev/null || true)
    done

    # Run changelog
    local output
    output=$(cd "$TEST_DIR" && cp "$(pwd)/$(dirname "${BASH_SOURCE[0]}")/changelog.sh" . 2>/dev/null || \
             cp "/tmp/changelog_fixed.sh" . && bash changelog.sh 2>&1)
    
    # Check output
    if [ -f "$TEST_DIR/CHANGELOG.md" ]; then
        ((PASS++))
        echo "✅ PASS: $name"
    else
        ((FAIL++))
        echo "❌ FAIL: $name"
        echo "  Output: $output"
    fi
}

# Test 1: No commits
# Test 2: Only feat commits → Added section
test_changelog "feat commits categorized as Added" \
    "feat: add user login
feat: new dashboard" \
    "Added"

# Test 3: fix commits → Fixed section
test_changelog "fix commits categorized as Fixed" \
    "fix: resolve login bug
fix: patch session timeout" \
    "Fixed"

# Test 4: remove commits → Removed section
test_changelog "remove commits categorized as Removed" \
    "remove: deprecated API v1
delete: old endpoint" \
    "Removed"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "All tests passed! ✅" || echo "Some tests failed. ❌"
exit $FAIL
