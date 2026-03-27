#!/usr/bin/env bash
# test-hook.sh — Verify pre-tool-use.sh blocks dangerous commands and allows safe ones
set -euo pipefail

HOOK="$(dirname "$0")/pre-tool-use.sh"
PASS=0; FAIL=0

run_test() {
  local desc="$1" expect_block="$2" json="$3"
  local result rc
  result=$(echo "$json" | bash "$HOOK" 2>&1) && rc=0 || rc=$?
  if [[ "$expect_block" == "block" && $rc -ne 0 ]]; then
    echo "  ✅ PASS (blocked): $desc"
    PASS=$((PASS+1))
  elif [[ "$expect_block" == "allow" && $rc -eq 0 ]]; then
    echo "  ✅ PASS (allowed): $desc"
    PASS=$((PASS+1))
  else
    echo "  ❌ FAIL: $desc (rc=$rc, expected=$expect_block)"
    echo "     Output: $result"
    FAIL=$((FAIL+1))
  fi
}

echo "Running pre-tool-use hook tests..."
echo ""

echo "--- Blocking tests ---"
run_test "rm -rf" "block" \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/data"}}'

run_test "rm -fr" "block" \
  '{"tool_name":"Bash","tool_input":{"command":"rm -fr /tmp/data"}}'

run_test "DROP TABLE" "block" \
  '{"tool_name":"Bash","tool_input":{"command":"DROP TABLE users;"}}'

run_test "git push --force" "block" \
  '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}'

run_test "git push -f" "block" \
  '{"tool_name":"Bash","tool_input":{"command":"git push -f origin main"}}'

run_test "TRUNCATE TABLE" "block" \
  '{"tool_name":"Bash","tool_input":{"command":"TRUNCATE TABLE logs;"}}'

run_test "DELETE FROM without WHERE" "block" \
  '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM sessions;"}}'

echo ""
echo "--- Allowing tests ---"
run_test "ls -la" "allow" \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'

run_test "rm single file" "allow" \
  '{"tool_name":"Bash","tool_input":{"command":"rm /tmp/old.txt"}}'

run_test "git push" "allow" \
  '{"tool_name":"Bash","tool_input":{"command":"git push origin main"}}'

run_test "DELETE with WHERE" "allow" \
  '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users WHERE id = 5;"}}'

run_test "Non-bash tool" "allow" \
  '{"tool_name":"Read","tool_input":{"file_path":"test.py"}}'

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
