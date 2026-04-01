#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# test-hook.sh — Test suite for guard-hook.sh
#
# Runs a series of commands through the hook and verifies that destructive
# commands are blocked and safe commands are allowed.
#
# Usage:
#   bash test-hook.sh
# ---------------------------------------------------------------------------

HOOK="$(dirname "$0")/guard-hook.sh"
PASS=0
FAIL=0
TOTAL=0

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Build a minimal JSON payload matching Claude Code's PreToolUse format
make_input() {
    local cmd="$1"
    # Escape double quotes and backslashes for JSON
    local escaped
    escaped="$(echo "$cmd" | sed 's/\\/\\\\/g; s/"/\\"/g')"
    printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$escaped"
}

# Run the hook with a command and capture exit code
run_hook() {
    local cmd="$1"
    local input
    input="$(make_input "$cmd")"
    echo "$input" | bash "$HOOK" 2>/dev/null
    return $?
}

assert_blocked() {
    local description="$1"
    local cmd="$2"
    TOTAL=$((TOTAL + 1))

    local exit_code=0
    run_hook "$cmd" || exit_code=$?

    if [[ $exit_code -eq 2 ]]; then
        echo -e "  ${GREEN}PASS${NC}  [BLOCKED] $description"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}FAIL${NC}  [BLOCKED] $description (expected exit 2, got $exit_code)"
        FAIL=$((FAIL + 1))
    fi
}

assert_allowed() {
    local description="$1"
    local cmd="$2"
    TOTAL=$((TOTAL + 1))

    local exit_code=0
    run_hook "$cmd" || exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        echo -e "  ${GREEN}PASS${NC}  [ALLOWED] $description"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}FAIL${NC}  [ALLOWED] $description (expected exit 0, got $exit_code)"
        FAIL=$((FAIL + 1))
    fi
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

echo ""
echo -e "${YELLOW}guard-hook.sh test suite${NC}"
echo "==========================================="
echo ""

echo "--- rm -rf ---"
assert_blocked "rm -rf /"               "rm -rf /"
assert_blocked "rm -rf /home/user"      "rm -rf /home/user"
assert_blocked "rm -rf ."               "rm -rf ."
assert_blocked "rm -fr /tmp/dir"        "rm -fr /tmp/dir"
assert_blocked "rm -rfi /some/path"     "rm -rfi /some/path"
assert_allowed "rm single file"         "rm file.txt"
assert_allowed "rm -r without -f"       "rm -r directory/"
assert_allowed "rm -f without -r"       "rm -f file.txt"

echo ""
echo "--- DROP TABLE / DATABASE ---"
assert_blocked "DROP TABLE users"       "DROP TABLE users;"
assert_blocked "drop table (lower)"     "drop table users;"
assert_blocked "DROP DATABASE"          "DROP DATABASE production;"
assert_blocked "DROP TABLE IF EXISTS"   "DROP TABLE IF EXISTS temp_data;"
assert_allowed "SELECT with drop word"  "SELECT * FROM dropdown_options;"
assert_allowed "Comment about dropping" "echo 'we should drop this feature'"

echo ""
echo "--- git push --force ---"
assert_blocked "git push --force"         "git push --force origin main"
assert_blocked "git push -f"              "git push -f origin main"
assert_blocked "git push origin main -f"  "git push origin main -f"
assert_allowed "git push (normal)"        "git push origin main"
assert_allowed "git push --force-with-lease"  "git push --force-with-lease origin main"

echo ""
echo "--- TRUNCATE ---"
assert_blocked "TRUNCATE TABLE"         "TRUNCATE TABLE users;"
assert_blocked "truncate table (lower)" "truncate table users;"
assert_blocked "TRUNCATE without TABLE" "TRUNCATE users;"
assert_allowed "Word truncate in text"  "echo 'truncate the string'"

echo ""
echo "--- DELETE FROM without WHERE ---"
assert_blocked "DELETE FROM users"             "DELETE FROM users;"
assert_blocked "delete from (lower)"           "delete from sessions;"
assert_allowed "DELETE FROM with WHERE"        "DELETE FROM users WHERE id = 5;"
assert_allowed "delete from with where (lower)" "delete from sessions where expired_at < now();"

echo ""
echo "--- Safe commands ---"
assert_allowed "ls"                     "ls -la"
assert_allowed "cat file"              "cat README.md"
assert_allowed "git status"            "git status"
assert_allowed "git commit"            "git commit -m 'fix: update'"
assert_allowed "npm install"           "npm install express"
assert_allowed "SELECT query"          "SELECT * FROM users WHERE id = 1;"
assert_allowed "INSERT INTO"           "INSERT INTO users (name) VALUES ('test');"
assert_allowed "UPDATE with WHERE"     "UPDATE users SET name = 'new' WHERE id = 1;"

echo ""
echo "==========================================="
echo -e "Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}, ${TOTAL} total"
echo ""

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
