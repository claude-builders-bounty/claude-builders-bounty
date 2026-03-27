#!/usr/bin/env bash
# test-hook.sh — Automated tests for guard-hook.sh
# Run: bash test-hook.sh

set -u

HOOK="$(dirname "$0")/guard-hook.sh"
PASS=0
FAIL=0
TOTAL=0

# Remove old test log if exists
rm -f "${HOME}/.claude/hooks/blocked.log"

assert_blocked() {
    local desc="$1"
    local json="$2"
    local expected_exit=2
    TOTAL=$((TOTAL + 1))

    local output
    output="$(printf '%s' "$json" | "$HOOK" 2>&1)"
    local actual_exit=$?

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        PASS=$((PASS + 1))
        printf "  PASS: %s (exit %d)\n" "$desc" "$actual_exit"
    else
        FAIL=$((FAIL + 1))
        printf "  FAIL: %s — expected exit %d, got %d\n" "$desc" "$expected_exit" "$actual_exit"
        printf "        output: %s\n" "$output"
    fi
}

assert_allowed() {
    local desc="$1"
    local json="$2"
    local expected_exit=0
    TOTAL=$((TOTAL + 1))

    local output
    output="$(printf '%s' "$json" | "$HOOK" 2>&1)"
    local actual_exit=$?

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        PASS=$((PASS + 1))
        printf "  PASS: %s (exit %d)\n" "$desc" "$actual_exit"
    else
        FAIL=$((FAIL + 1))
        printf "  FAIL: %s — expected exit %d, got %d\n" "$desc" "$expected_exit" "$actual_exit"
        printf "        output: %s\n" "$output"
    fi
}

echo "======================================"
echo "guard-hook.sh test suite"
echo "======================================"
echo ""

echo "--- SHOULD BE BLOCKED (exit 2) ---"
assert_blocked "rm -rf /"            '{"tool_input":{"command":"rm -rf /"},"cwd":"/tmp"}'
assert_blocked "rm -rf ."            '{"tool_input":{"command":"rm -rf ."},"cwd":"/tmp"}'
assert_blocked "rm -rf /tmp/data"    '{"tool_input":{"command":"rm -rf /tmp/data"},"cwd":"/tmp"}'
assert_blocked "rm -fr /stuff"       '{"tool_input":{"command":"rm -fr /stuff"},"cwd":"/tmp"}'
assert_blocked "rm -r -f /data"      '{"tool_input":{"command":"rm -r -f /data"},"cwd":"/tmp"}'
assert_blocked "rm -f -r /data"      '{"tool_input":{"command":"rm -f -r /data"},"cwd":"/tmp"}'
assert_blocked "rm --recursive --force /x" '{"tool_input":{"command":"rm --recursive --force /x"},"cwd":"/tmp"}'
assert_blocked "rm --force --recursive /x" '{"tool_input":{"command":"rm --force --recursive /x"},"cwd":"/tmp"}'
assert_blocked "DROP TABLE users"    '{"tool_input":{"command":"mysql -e \"DROP TABLE users;\""},"cwd":"/tmp"}'
assert_blocked "drop table lower"    '{"tool_input":{"command":"psql -c \"drop table orders\""},"cwd":"/tmp"}'
assert_blocked "git push --force"    '{"tool_input":{"command":"git push --force origin main"},"cwd":"/tmp"}'
assert_blocked "git push -f"         '{"tool_input":{"command":"git push -f origin main"},"cwd":"/tmp"}'
assert_blocked "git push origin -f"  '{"tool_input":{"command":"git push origin main -f"},"cwd":"/tmp"}'
assert_blocked "TRUNCATE TABLE"      '{"tool_input":{"command":"psql -c \"TRUNCATE TABLE orders\""},"cwd":"/tmp"}'
assert_blocked "truncate lower"      '{"tool_input":{"command":"mysql -e \"truncate table users\""},"cwd":"/tmp"}'
assert_blocked "DELETE FROM no WHERE" '{"tool_input":{"command":"sqlite3 db \"DELETE FROM users;\""},"cwd":"/tmp"}'
assert_blocked "delete from lower"   '{"tool_input":{"command":"psql -c \"delete from orders;\""},"cwd":"/tmp"}'
echo ""

echo "--- SHOULD BE ALLOWED (exit 0) ---"
assert_allowed "ls -la"              '{"tool_input":{"command":"ls -la"},"cwd":"/tmp"}'
assert_allowed "rm single file"      '{"tool_input":{"command":"rm /tmp/file.txt"},"cwd":"/tmp"}'
assert_allowed "rm -r (no force)"    '{"tool_input":{"command":"rm -r /tmp/dir"},"cwd":"/tmp"}'
assert_allowed "rm -f (no recurse)"  '{"tool_input":{"command":"rm -f /tmp/file"},"cwd":"/tmp"}'
assert_allowed "git push normal"     '{"tool_input":{"command":"git push origin main"},"cwd":"/tmp"}'
assert_allowed "git push -u"         '{"tool_input":{"command":"git push -u origin feature"},"cwd":"/tmp"}'
assert_allowed "git push --force-with-lease" '{"tool_input":{"command":"git push --force-with-lease origin main"},"cwd":"/tmp"}'
assert_allowed "DELETE with WHERE"   '{"tool_input":{"command":"sqlite3 db \"DELETE FROM users WHERE id = 5;\""},"cwd":"/tmp"}'
assert_allowed "npm install"         '{"tool_input":{"command":"npm install express"},"cwd":"/tmp"}'
assert_allowed "git status"          '{"tool_input":{"command":"git status"},"cwd":"/tmp"}'
assert_allowed "empty command"       '{"tool_input":{"command":""},"cwd":"/tmp"}'
assert_allowed "no command field"    '{"tool_input":{},"cwd":"/tmp"}'
assert_allowed "python script"       '{"tool_input":{"command":"python3 app.py"},"cwd":"/tmp"}'
assert_allowed "docker build"        '{"tool_input":{"command":"docker build -t myapp ."},"cwd":"/tmp"}'
echo ""

echo "======================================"
printf "RESULTS: %d/%d passed" "$PASS" "$TOTAL"
if [ "$FAIL" -gt 0 ]; then
    printf " (%d FAILED)" "$FAIL"
fi
echo ""
echo "======================================"

# Check log file
if [ -f "${HOME}/.claude/hooks/blocked.log" ]; then
    LOGCOUNT=$(wc -l < "${HOME}/.claude/hooks/blocked.log")
    echo ""
    echo "Log file: ${HOME}/.claude/hooks/blocked.log ($LOGCOUNT entries)"
    echo "Sample entry:"
    head -1 "${HOME}/.claude/hooks/blocked.log"
fi

exit "$FAIL"
