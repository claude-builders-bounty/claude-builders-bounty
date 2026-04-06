#!/bin/bash
# Test suite for Claude Safety Hook

set -e

HOOK_PATH="$HOME/.claude/hooks/pre_tool_use.py"

echo "🧪 Claude Safety Hook Test Suite"
echo "================================"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test a command
test_command() {
    local command="$1"
    local expected="$2"  # "block" or "allow"
    local description="$3"

    echo -n "Testing: $description ... "

    # Prepare input
    input=$(cat <<EOF
{
  "tool_name": "bash",
  "tool_input": {
    "command": "$command"
  }
}
EOF
)

    # Run hook
    output=$(echo "$input" | python3 "$HOOK_PATH" 2>&1)
    exit_code=$?

    # Check result
    if [ "$expected" = "block" ]; then
        if echo "$output" | grep -q '"continue": false'; then
            echo "✅ PASS (blocked)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo "❌ FAIL (should have blocked)"
            echo "   Output: $output"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        if echo "$output" | grep -q '"continue": true'; then
            echo "✅ PASS (allowed)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo "❌ FAIL (should have allowed)"
            echo "   Output: $output"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
}

echo "### 🛡️  Testing Dangerous Commands (should block)"
echo ""

test_command "rm -rf /tmp/test" "block" "rm -rf with path"
test_command "rm -fr /home/user/data" "block" "rm -fr variant"
test_command "DROP TABLE users" "block" "DROP TABLE"
test_command "DROP DATABASE production" "block" "DROP DATABASE"
test_command "TRUNCATE TABLE logs" "block" "TRUNCATE TABLE"
test_command "TRUNCATE users" "block" "TRUNCATE without TABLE"
test_command "DELETE FROM users" "block" "DELETE FROM without WHERE"
test_command "DELETE FROM users;" "block" "DELETE FROM with semicolon"
test_command "git push --force" "block" "git push --force"
test_command "git push -f origin main" "block" "git push -f"

echo ""
echo "### ✅ Testing Safe Commands (should allow)"
echo ""

test_command "echo hello" "allow" "Simple echo"
test_command "ls -la" "allow" "List files"
test_command "rm test.txt" "allow" "rm without -rf"
test_command "DROP COLUMN age" "allow" "DROP COLUMN (not TABLE)"
test_command "DELETE FROM users WHERE id = 1" "allow" "DELETE with WHERE"
test_command "git push" "allow" "git push without --force"
test_command "git push origin main" "allow" "git push to specific branch"
test_command "docker ps" "allow" "Docker command"
test_command "python3 script.py" "allow" "Python script"

echo ""
echo "================================"
echo "📊 Test Results"
echo "================================"
echo "✅ Passed: $TESTS_PASSED"
echo "❌ Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed. Please review the output above."
    exit 1
fi
