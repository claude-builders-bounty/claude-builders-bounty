#!/bin/bash
# Test suite for pre_tool_use_hook.py

echo "=== Pre-tool-use Hook Test Suite ==="
echo ""

PASS=0
FAIL=0

run_test() {
    local name="$1"
    local cmd="$2"
    local expect_block="$3"  # "block" or "allow"

    result=$(echo "$cmd" | python3 pre_tool_use_hook.py 2>&1)
    exit_code=$?

    if [ "$expect_block" = "block" ]; then
        if [ $exit_code -eq 1 ]; then
            echo "✅ PASS: $name (blocked as expected)"
            ((PASS++))
        else
            echo "❌ FAIL: $name (should have been blocked)"
            ((FAIL++))
        fi
    else
        if [ $exit_code -eq 0 ]; then
            echo "✅ PASS: $name (allowed as expected)"
            ((PASS++))
        else
            echo "❌ FAIL: $name (should have been allowed)"
            ((FAIL++))
        fi
    fi
}

# Test blocked commands
run_test "rm -rf /" '{"tool":"Bash","toolInput":{"command":"rm -rf /"}}' "block"
run_test "rm -rf /var" '{"tool":"Bash","toolInput":{"command":"rm -rf /var"}}' "block"
run_test "DROP TABLE users" '{"tool":"Bash","toolInput":{"command":"DROP TABLE users"}}' "block"
run_test "TRUNCATE TABLE sessions" '{"tool":"Bash","toolInput":{"command":"TRUNCATE TABLE sessions"}}' "block"
run_test "DELETE FROM without WHERE" '{"tool":"Bash","toolInput":{"command":"DELETE FROM users"}}' "block"
run_test "git push --force" '{"tool":"Bash","toolInput":{"command":"git push --force origin main"}}' "block"
run_test "git push -f" '{"tool":"Bash","toolInput":{"command":"git push -f"}}' "block"
run_test "DROP without WHERE" '{"tool":"Bash","toolInput":{"command":"DROP database production"}}' "block"

# Test allowed commands
run_test "safe ls" '{"tool":"Bash","toolInput":{"command":"ls -la"}}' "allow"
run_test "safe git commit" '{"tool":"Bash","toolInput":{"command":"git commit -m fix"}}' "allow"
run_test "safe git push" '{"tool":"Bash","toolInput":{"command":"git push origin main"}}' "allow"
run_test "safe DELETE with WHERE" '{"tool":"Bash","toolInput":{"command":"DELETE FROM users WHERE id=1"}}' "allow"
run_test "node script.js" '{"tool":"Bash","toolInput":{"command":"node script.js"}}' "allow"
run_test "cat file.txt" '{"tool":"Bash","toolInput":{"command":"cat /etc/hostname"}}' "allow"
run_test "rm file.txt" '{"tool":"Bash","toolInput":{"command":"rm -i file.txt"}}' "allow"

# Test non-Bash tools (should always allow)
run_test "Read tool (ignore)" '{"tool":"Read","toolInput":{"file_path":"/etc/passwd"}}' "allow"
run_test "Write tool (ignore)" '{"tool":"Write","toolInput":{"path":"/etc/passwd"}}' "allow"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
