#!/usr/bin/env bash
# Test suite for block-destructive.sh hook
# Run: bash tests/test_hook.sh

set -uo pipefail

HOOK="./hook.sh"
PASS=0
FAIL=0

assert_block() {
    local desc="$1"
    local cmd="$2"
    local result
    result=$(echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$cmd\"}}" | bash "$HOOK" 2>/dev/null)
    if echo "$result" | grep -q '"block"'; then
        echo "✅ PASS (blocked): $desc"
        ((PASS++))
    else
        echo "❌ FAIL (not blocked): $desc → $result"
        ((FAIL++))
    fi
}

assert_allow() {
    local desc="$1"
    local cmd="$2"
    local result
    result=$(echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$cmd\"}}" | bash "$HOOK" 2>/dev/null)
    if echo "$result" | grep -q '"allow"'; then
        echo "✅ PASS (allowed): $desc"
        ((PASS++))
    else
        echo "❌ FAIL (blocked): $desc → $result"
        ((FAIL++))
    fi
}

# --- Tests ---

echo "🧪 Testing destructive command blocking..."
echo ""

# Should BLOCK
assert_block "rm -rf with path" "rm -rf /home/user/project"
assert_block "rm -fr variant" "rm -fr node_modules"
assert_block "DROP TABLE" "DROP TABLE users;"
assert_block "drop table lowercase" "drop table if exists customers;"
assert_block "TRUNCATE TABLE" "TRUNCATE TABLE logs;"
assert_block "TRUNCATE alone" "TRUNCATE session_data;"
assert_block "DELETE FROM without WHERE" "DELETE FROM users;"
assert_block "git push --force" "git push --force origin main"
assert_block "git push -f" "git push -f origin main"

echo ""

# Should ALLOW
assert_allow "ls command" "ls -la"
assert_allow "git status" "git status"
assert_allow "normal push" "git push origin main"
assert_allow "DELETE with WHERE" "DELETE FROM users WHERE id = 5;"
assert_allow "rm single file" "rm old_file.txt"
assert_allow "pip install" "pip install requests"
assert_allow "mkdir" "mkdir -p new_directory"
assert_allow "cat file" "cat /etc/hosts"

echo ""
echo "═══════════════════════════════════"
echo "Results: ✅ $PASS passed  ❌ $FAIL failed"
echo "═══════════════════════════════════"

# Show blocked log
if [ -f "$HOME/.claude/hooks/blocked.log" ]; then
    echo ""
    echo "📋 Blocked log entries:"
    tail -5 "$HOME/.claude/hooks/blocked.log"
fi

exit $FAIL
