#!/bin/bash
# Simple test script for the block-destructive-commands hook

HOOK_SCRIPT="./pre-tool-use.sh"

echo "Testing block-destructive-commands hook..."
echo ""

# Test 1: Safe command should pass
echo "Test 1: Safe command (ls -la)"
echo '{"tool_name": "Bash", "tool_input": {"command": "ls -la"}}' | "$HOOK_SCRIPT" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PASS: Safe command allowed"
else
    echo "❌ FAIL: Safe command was blocked"
fi
echo ""

# Test 2: rm -rf should be blocked
echo "Test 2: Dangerous command (rm -rf /tmp/test)"
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/test"}}' | "$HOOK_SCRIPT" > /dev/null 2>&1
if [ $? -eq 2 ]; then
    echo "✅ PASS: rm -rf was blocked"
else
    echo "❌ FAIL: rm -rf was not blocked"
fi
echo ""

# Test 3: DROP TABLE should be blocked
echo "Test 3: Dangerous SQL (DROP TABLE users)"
echo '{"tool_name": "Bash", "tool_input": {"command": "psql -c \"DROP TABLE users;\""}}' | "$HOOK_SCRIPT" > /dev/null 2>&1
if [ $? -eq 2 ]; then
    echo "✅ PASS: DROP TABLE was blocked"
else
    echo "❌ FAIL: DROP TABLE was not blocked"
fi
echo ""

# Test 4: git push --force should be blocked
echo "Test 4: Dangerous git (git push --force origin main)"
echo '{"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}}' | "$HOOK_SCRIPT" > /dev/null 2>&1
if [ $? -eq 2 ]; then
    echo "✅ PASS: git push --force was blocked"
else
    echo "❌ FAIL: git push --force was not blocked"
fi
echo ""

# Test 5: DELETE FROM without WHERE should be blocked
echo "Test 5: Dangerous SQL (DELETE FROM users)"
echo '{"tool_name": "Bash", "tool_input": {"command": "psql -c \"DELETE FROM users;\""}}' | "$HOOK_SCRIPT" > /dev/null 2>&1
if [ $? -eq 2 ]; then
    echo "✅ PASS: DELETE FROM without WHERE was blocked"
else
    echo "❌ FAIL: DELETE FROM without WHERE was not blocked"
fi
echo ""

# Test 6: DELETE FROM with WHERE should pass
echo "Test 6: Safe SQL (DELETE FROM users WHERE id = 1)"
echo '{"tool_name": "Bash", "tool_input": {"command": "psql -c \"DELETE FROM users WHERE id = 1;\""}}' | "$HOOK_SCRIPT" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PASS: DELETE FROM with WHERE allowed"
else
    echo "❌ FAIL: DELETE FROM with WHERE was blocked"
fi
echo ""

echo "All tests completed!"
