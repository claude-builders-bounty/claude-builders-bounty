#!/usr/bin/env bash
# test.sh — Validates guard.sh against dangerous and safe commands
#
# Usage: bash test.sh
#
# Runs guard.sh with simulated tool inputs and checks exit codes.
# Exit code 0 = all tests passed, 1 = some tests failed.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARD="$SCRIPT_DIR/guard.sh"
PASS=0
FAIL=0

# Use a temp log file so tests don't pollute the real log
export CLAUDE_HOOKS_DIR="$(mktemp -d)"
trap 'rm -rf "$CLAUDE_HOOKS_DIR"' EXIT

# ---------------------------------------------------------------------------
# Helper: run guard.sh with a simulated Bash tool input
# ---------------------------------------------------------------------------
run_test() {
    local description="$1"
    local command="$2"
    local expected_exit="$3"  # 0 = should allow, 2 = should block

    local input
    input=$(printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$command")

    local actual_exit
    printf '%s' "$input" | bash "$GUARD" >/dev/null 2>&1
    actual_exit=$?

    if [[ "$actual_exit" -eq "$expected_exit" ]]; then
        printf '  PASS: %s\n' "$description"
        ((PASS++))
    else
        printf '  FAIL: %s (expected exit %d, got %d)\n' "$description" "$expected_exit" "$actual_exit"
        ((FAIL++))
    fi
}

# ---------------------------------------------------------------------------
# Helper: run guard.sh with a non-Bash tool (should always allow)
# ---------------------------------------------------------------------------
run_non_bash_test() {
    local description="$1"
    local tool_name="$2"

    local input
    input=$(printf '{"tool_name":"%s","tool_input":{"command":"rm -rf /"}}' "$tool_name")

    local actual_exit
    printf '%s' "$input" | bash "$GUARD" >/dev/null 2>&1
    actual_exit=$?

    if [[ "$actual_exit" -eq 0 ]]; then
        printf '  PASS: %s\n' "$description"
        ((PASS++))
    else
        printf '  FAIL: %s (expected exit 0, got %d)\n' "$description" "$actual_exit"
        ((FAIL++))
    fi
}

echo "=== Destructive Command Guard — Test Suite ==="
echo ""

# --- Non-Bash tools should pass through ---
echo "[Non-Bash tools]"
run_non_bash_test "Read tool is not intercepted" "Read"
run_non_bash_test "Edit tool is not intercepted" "Edit"
run_non_bash_test "Grep tool is not intercepted" "Grep"
echo ""

# --- rm -rf dangerous targets ---
echo "[rm -rf dangerous targets — should BLOCK]"
run_test "rm -rf /" "rm -rf /" 2
run_test "rm -rf ~" "rm -rf ~" 2
run_test "rm -rf ." "rm -rf ." 2
run_test "rm -rf / with extra spaces" "rm  -rf  /" 2
run_test "rm -rf /*" "rm -rf /*" 2
echo ""

echo "[rm -rf safe targets — should ALLOW]"
run_test "rm -rf node_modules/" "rm -rf node_modules/" 0
run_test "rm -rf ./dist" "rm -rf ./dist" 0
run_test "rm -rf /tmp/build" "rm -rf /tmp/build" 0
run_test "rm -rf specific-dir" "rm -rf some-directory" 0
echo ""

# --- DROP TABLE ---
echo "[DROP TABLE — should BLOCK]"
run_test "DROP TABLE users" "sqlite3 test.db 'DROP TABLE users'" 2
run_test "drop table (lowercase)" "psql -c 'drop table users'" 2
run_test "DROP TABLE with IF EXISTS" "mysql -e 'DROP TABLE IF EXISTS temp'" 2
echo ""

# --- TRUNCATE ---
echo "[TRUNCATE — should BLOCK]"
run_test "TRUNCATE TABLE users" "psql -c 'TRUNCATE TABLE users'" 2
run_test "truncate (lowercase)" "mysql -e 'truncate logs'" 2
echo ""

# --- DELETE FROM ---
echo "[DELETE FROM — should BLOCK without WHERE]"
run_test "DELETE FROM users (no WHERE)" "psql -c 'DELETE FROM users'" 2
run_test "delete from (lowercase, no WHERE)" "sqlite3 db 'delete from logs'" 2
echo ""

echo "[DELETE FROM with WHERE — should ALLOW]"
run_test "DELETE FROM users WHERE id=1" "psql -c 'DELETE FROM users WHERE id = 1'" 0
run_test "delete from with where (lowercase)" "sqlite3 db 'delete from logs where age > 30'" 0
echo ""

# --- git push --force ---
echo "[git push --force — should BLOCK]"
run_test "git push --force origin main" "git push --force origin main" 2
run_test "git push -f origin master" "git push -f origin master" 2
run_test "git push --force (bare)" "git push --force" 2
run_test "git push -f (bare)" "git push -f" 2
echo ""

echo "[git push safe variants — should ALLOW]"
run_test "git push origin main (no force)" "git push origin main" 0
run_test "git push (no force)" "git push" 0
run_test "git push --force origin feature-branch" "git push --force origin feature-branch" 0
echo ""

# --- Normal commands should pass ---
echo "[Normal commands — should ALLOW]"
run_test "ls -la" "ls -la" 0
run_test "git status" "git status" 0
run_test "npm install" "npm install" 0
run_test "cat file.txt" "cat file.txt" 0
run_test "mkdir -p /tmp/test" "mkdir -p /tmp/test" 0
run_test "echo hello world" "echo hello world" 0
echo ""

# --- Check that log file was created ---
echo "[Logging]"
if [[ -f "$CLAUDE_HOOKS_DIR/blocked.log" ]]; then
    LINES="$(wc -l < "$CLAUDE_HOOKS_DIR/blocked.log" | tr -d ' ')"
    printf '  PASS: blocked.log exists with %s entries\n' "$LINES"
    ((PASS++))
else
    printf '  FAIL: blocked.log was not created\n'
    ((FAIL++))
fi
echo ""

# --- Summary ---
echo "=== Results: $PASS passed, $FAIL failed ==="
if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
exit 0
