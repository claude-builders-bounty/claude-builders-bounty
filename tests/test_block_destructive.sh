#!/usr/bin/env bash
# Test suite for block-destructive-bash.sh hook

set -u

HOOK_SCRIPT="./hooks/block-destructive-bash.sh"
chmod +x "${HOOK_SCRIPT}"

PASSED=0
FAILED=0

assert_blocked() {
    local cmd="$1"
    local desc="$2"
    if echo "{\"command\": \"${cmd}\"}" | bash "${HOOK_SCRIPT}" >/dev/null 2>&1; then
        echo "❌ FAILED: Expected BLOCKED for: ${desc} ('${cmd}')"
        FAILED=$((FAILED + 1))
    else
        echo "✅ PASSED: Blocked: ${desc}"
        PASSED=$((PASSED + 1))
    fi
}

assert_allowed() {
    local cmd="$1"
    local desc="$2"
    if echo "{\"command\": \"${cmd}\"}" | bash "${HOOK_SCRIPT}" >/dev/null 2>&1; then
        echo "✅ PASSED: Allowed: ${desc}"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAILED: Expected ALLOWED for: ${desc} ('${cmd}')"
        FAILED=$((FAILED + 1))
    fi
}

echo "=== RUNNING HOOK SAFETY TESTS ==="

# Destructive test cases (Must be blocked)
assert_blocked "rm -rf /" "Root directory removal"
assert_blocked "rm -rf *" "Current directory wildcard removal"
assert_blocked "rm -fr ./build" "Inverted flag rm -fr"
assert_blocked "git push origin main --force" "Git force push"
assert_blocked "git push -f origin main" "Git short force push"
assert_blocked "DROP TABLE users;" "SQL DROP TABLE"
assert_blocked "drop database production;" "SQL DROP DATABASE case-insensitive"
assert_blocked "TRUNCATE TABLE logs;" "SQL TRUNCATE TABLE"
assert_blocked "DELETE FROM customers;" "Unbounded SQL DELETE without WHERE"
assert_blocked "dd if=/dev/zero of=/dev/sda" "Raw disk zeroing"
assert_blocked "mkfs.ext4 /dev/sdb1" "Disk format"

# Safe test cases (Must be allowed)
assert_allowed "ls -la" "List directory"
assert_allowed "git status" "Git status"
assert_allowed "git push origin feat/branch" "Normal git push"
assert_allowed "rm temp.txt" "Single file removal without -r"
assert_allowed "DELETE FROM customers WHERE id = 42;" "Bounded SQL DELETE with WHERE"
assert_allowed "npm run build" "Build command"
assert_allowed "pytest tests/" "Run tests"

echo "================================="
echo "Test Summary: ${PASSED} passed, ${FAILED} failed"

if [ "${FAILED}" -ne 0 ]; then
    exit 1
fi
exit 0
