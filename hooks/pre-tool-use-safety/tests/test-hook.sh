#!/usr/bin/env bash
# Test suite for pre-tool-use-safety hook.
# Runs 17 cases — 10 dangerous (must block) + 7 safe (must pass).
# Exit code 0 if all pass, 1 if any fail.
# Zero external dependencies: bash + grep.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="${SCRIPT_DIR}/../hook.sh"

if [[ ! -x "${HOOK}" ]]; then
    chmod +x "${HOOK}" 2>/dev/null || {
        echo "ERROR: hook.sh not found or not executable: ${HOOK}"
        exit 1
    }
fi

PASS=0
FAIL=0

# Escape a string for embedding in a JSON string literal
js_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    printf '%s' "${s}"
}

# Run hook with a Bash command payload. Return 0 if denied, 1 if allowed.
run_hook() {
    local cmd="$1"
    local cmd_esc
    cmd_esc="$(js_escape "${cmd}")"
    local payload="{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"${cmd_esc}\"},\"cwd\":\"/tmp/test\"}"
    local output
    output="$(printf '%s' "${payload}" | "${HOOK}" 2>/dev/null)"
    if echo "${output}" | grep -q '"permissionDecision"[[:space:]]*:[[:space:]]*"deny"'; then
        return 0
    fi
    return 1
}

assert_blocked() {
    local desc="$1"
    local cmd="$2"
    if run_hook "${cmd}"; then
        echo "  PASS [blocked]   ${desc}"
        PASS=$((PASS + 1))
    else
        echo "  FAIL [expected block]  ${desc}: ${cmd}"
        FAIL=$((FAIL + 1))
    fi
}

assert_allowed() {
    local desc="$1"
    local cmd="$2"
    if run_hook "${cmd}"; then
        echo "  FAIL [expected allow]  ${desc}: ${cmd}"
        FAIL=$((FAIL + 1))
    else
        echo "  PASS [allowed]   ${desc}"
        PASS=$((PASS + 1))
    fi
}

echo "=== Dangerous commands (should be BLOCKED) ==="
assert_blocked "rm -rf"                       "rm -rf /tmp/test"
assert_blocked "rm -fr (flag order)"          "rm -fr node_modules"
assert_blocked "DROP TABLE"                   "sqlite3 app.db 'DROP TABLE users;'"
assert_blocked "drop table (lowercase)"       "sqlite3 app.db 'drop table users;'"
assert_blocked "TRUNCATE"                     "psql -c 'TRUNCATE TABLE sessions;'"
assert_blocked "DELETE FROM without WHERE"    "psql -c 'DELETE FROM users;'"
assert_blocked "git push --force"             "git push --force origin main"
assert_blocked "git push -f"                  "git push -f origin develop"
assert_blocked "mkfs"                         "sudo mkfs.ext4 /dev/sdb1"
assert_blocked "chmod -R 777 /"               "chmod -R 777 /"

echo ""
echo "=== Safe commands (should be ALLOWED) ==="
assert_allowed "ls"                           "ls -la"
assert_allowed "npm install"                  "npm install"
assert_allowed "git push (no --force)"        "git push origin main"
assert_allowed "DELETE FROM with WHERE"       "psql -c 'DELETE FROM users WHERE id=1;'"
assert_allowed "rm specific file"             "rm /tmp/foo.txt"
assert_allowed "find with -delete"            "find /tmp -name '*.log' -delete"
assert_allowed "node version check"           "node --version"

echo ""
echo "=== Results ==="
echo "Passed: ${PASS}"
echo "Failed: ${FAIL}"

if [[ ${FAIL} -gt 0 ]]; then
    exit 1
fi
exit 0
