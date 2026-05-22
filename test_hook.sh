#!/usr/bin/env bash
# Test suite for the pre-tool-use hook.
# Verifies dangerous commands are blocked and safe commands pass through.

set -euo pipefail

HOOK="hooks/pre-tool-use.py"
PASS=0
FAIL=0

run_test() {
    local description="$1"
    local tool_name="$2"
    local command="$3"
    local expect_block="$4"  # "yes" or "no"

    local input
    input=$(printf '{"tool_name":"%s","tool_input":{"command":"%s"}}' "$tool_name" "$command")

    local exit_code=0
    local output
    output=$(echo "$input" | python "$HOOK" 2>&1) || exit_code=$?

    if [ "$expect_block" = "yes" ]; then
        if [ "$exit_code" -ne 0 ]; then
            echo "  ✅ PASS: $description (blocked, exit=$exit_code)"
            PASS=$((PASS + 1))
        else
            echo "  ❌ FAIL: $description (expected block, got exit=0)"
            FAIL=$((FAIL + 1))
        fi
    else
        if [ "$exit_code" -eq 0 ]; then
            echo "  ✅ PASS: $description (allowed, exit=0)"
            PASS=$((PASS + 1))
        else
            echo "  ❌ FAIL: $description (expected allow, got exit=$exit_code)"
            echo "     Output: $output"
            FAIL=$((FAIL + 1))
        fi
    fi
}

echo ""
echo "=== Pre-tool-use Hook Test Suite ==="
echo ""

echo "--- Dangerous commands (should be BLOCKED) ---"
run_test "rm -rf /"                       "Bash" "rm -rf /"                          "yes"
run_test "rm -rf /home/user"              "Bash" "rm -rf /home/user"                 "yes"
run_test "rm -f important.txt"            "Bash" "rm -f important.txt"               "yes"
run_test "rm --no-preserve-root /"        "Bash" "rm --no-preserve-root /"           "yes"
run_test "DROP TABLE users"               "Bash" "psql -c 'DROP TABLE users'"        "yes"
run_test "drop table (lowercase)"         "Bash" "mysql -e 'drop table accounts'"    "yes"
run_test "git push --force"               "Bash" "git push --force origin main"      "yes"
run_test "git push -f"                    "Bash" "git push -f origin main"           "yes"
run_test "TRUNCATE TABLE logs"            "Bash" "psql -c 'TRUNCATE TABLE logs'"     "yes"
run_test "DELETE FROM without WHERE"      "Bash" "psql -c 'DELETE FROM users'"       "yes"

echo ""
echo "--- Safe commands (should be ALLOWED) ---"
run_test "ls -la"                         "Bash" "ls -la"                            "no"
run_test "git push (normal)"              "Bash" "git push origin main"              "no"
run_test "git status"                     "Bash" "git status"                        "no"
run_test "rm single file (no -f)"         "Bash" "rm temp.txt"                       "no"
run_test "DELETE FROM with WHERE"         "Bash" "psql -c 'DELETE FROM users WHERE id=1'" "no"
run_test "echo harmless"                  "Bash" "echo hello world"                  "no"
run_test "python script"                  "Bash" "python main.py"                    "no"
run_test "npm install"                    "Bash" "npm install express"               "no"

echo ""
echo "--- Non-Bash tools (should be ALLOWED) ---"
run_test "Read tool ignored"              "Read"  "rm -rf /"                         "no"
run_test "Write tool ignored"             "Write" "DROP TABLE users"                 "no"

echo ""
echo "--- Edge cases ---"
run_test "Empty command"                  "Bash" ""                                  "no"

echo ""
echo "--- Logging check ---"
LOG_FILE="$HOME/.claude/hooks/blocked.log"
if [ -f "$LOG_FILE" ]; then
    LINES=$(wc -l < "$LOG_FILE")
    echo "  ✅ blocked.log exists with $LINES entries"
    echo "  Last entry:"
    tail -1 "$LOG_FILE" | sed 's/^/     /'
else
    echo "  ❌ blocked.log not found at $LOG_FILE"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    echo "❌ SOME TESTS FAILED"
    exit 1
else
    echo "✅ ALL TESTS PASSED"
    exit 0
fi
