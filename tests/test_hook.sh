#!/usr/bin/env bash
# ==============================================================================
# Test Suite: test_hook.sh
# Validates hooks/block-destructive.sh against dangerous & safe command sets
# ==============================================================================

set -uo pipefail

HOOK_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/hooks/block-destructive.sh"

if [[ ! -f "$HOOK_SCRIPT" ]]; then
    echo "❌ Error: Hook script not found at $HOOK_SCRIPT"
    exit 1
fi

chmod +x "$HOOK_SCRIPT"

PASSED_TESTS=0
FAILED_TESTS=0
TOTAL_TESTS=0

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

run_test() {
    local cmd="$1"
    local expected_status="$2" # 0 = safe/allowed, 1 = dangerous/blocked
    local desc="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Run hook script passing command as argument
    set +e
    "$HOOK_SCRIPT" "$cmd" >/dev/null 2>&1
    local actual_status=$?
    set -e

    if [[ $actual_status -eq $expected_status ]]; then
        echo -e "${GREEN}✓ [PASS]${NC} $desc: \`$cmd\`"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ [FAIL]${NC} $desc: \`$cmd\` (expected $expected_status, got $actual_status)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo "============================================================"
echo " Running Destructive Command Hook Test Suite"
echo " Target: $HOOK_SCRIPT"
echo "============================================================"
echo ""

echo "--- 🚫 Section 1: Dangerous Commands (Expected to BLOCK / exit 1) ---"
run_test "rm -rf /" 1 "Root directory deletion"
run_test "rm -rf /*" 1 "Root wildcard deletion"
run_test "rm -rf ~" 1 "Home directory deletion"
run_test "rm -rf ~/" 1 "Home trailing slash deletion"
run_test "rm -rf *" 1 "Current directory wildcard deletion"
run_test "rm -rf ./*" 1 "Current directory relative wildcard deletion"
run_test "rm -rf .." 1 "Parent directory deletion"
run_test "git push -f origin main" 1 "Force push to main"
run_test "git push --force origin master" 1 "Force push to master"
run_test "git push -f origin prod" 1 "Force push to prod"
run_test "git push origin +main" 1 "Plus-prefix force push to main"
run_test "mkfs.ext4 /dev/sda1" 1 "Direct mkfs format"
run_test "dd if=/dev/zero of=/dev/sda bs=1M" 1 "Raw disk overwrite with dd"
run_test "chmod -R 777 /" 1 "Root permission wipeout"
run_test "chmod -R 777 /etc" 1 "System etc permission change"
run_test "chown -R root:root /" 1 "Root ownership wipeout"
run_test "DROP DATABASE production;" 1 "SQL drop database"
run_test "DROP TABLE users;" 1 "SQL drop table"
run_test "TRUNCATE TABLE accounts;" 1 "SQL truncate table"
run_test "shutdown -h now" 1 "System shutdown command"
run_test ":(){ :|:& };:" 1 "Fork bomb attempt"

echo ""
echo "--- ✅ Section 2: Safe Scoped Commands (Expected to PASS / exit 0) ---"
run_test "rm -rf node_modules" 0 "Scoped node_modules cleanup"
run_test "rm -rf dist build .next" 0 "Scoped build artifacts cleanup"
run_test "rm -rf /tmp/test-cache" 0 "Scoped /tmp cache cleanup"
run_test "rm file.txt" 0 "Single file removal"
run_test "git push origin feat/destructive-command-hook" 0 "Standard feature branch git push"
run_test "git push -u origin feature/my-cool-feature" 0 "Upstream tracking git push"
run_test "git push -f origin feat/my-scratch-branch" 0 "Force push to non-protected branch"
run_test "git status" 0 "Git status check"
run_test "npm run build" 0 "Standard build command"
run_test "npm test" 0 "Standard test runner"
run_test "dd if=/dev/urandom of=./dummy.bin bs=1M count=5" 0 "Local file generation via dd"
run_test "chmod +x hooks/block-destructive.sh" 0 "Local script chmod"
run_test "chmod -R 755 ./public" 0 "Scoped directory permissions"
run_test "SELECT * FROM users WHERE active = true;" 0 "Safe SQL query"
run_test "CREATE TABLE IF NOT EXISTS logs (id INT);" 0 "Safe SQL create table"
run_test "ls -la /var/log" 0 "Listing directory contents"

echo ""
echo "============================================================"
echo " Test Results: $PASSED_TESTS/$TOTAL_TESTS passed ($FAILED_TESTS failed)"
echo "============================================================"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}🎉 All tests passed successfully with 100% pass rate!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi
