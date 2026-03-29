#!/bin/bash
# test-block-destructive.sh — Tests for the block-destructive hook
#
# Runs the hook with simulated Claude Code JSON input and checks results.
# Requires: jq, bash

set -euo pipefail

HOOK="$(cd "$(dirname "$0")" && pwd)/block-destructive.sh"
PASS=0
FAIL=0

# --- Test helpers ---
run_hook() {
  local command="$1"
  local json
  json=$(jq -n --arg cmd "$command" '{
    tool_name: "Bash",
    tool_input: { command: $cmd },
    session: { project_directory: "/tmp/test-project" }
  }')
  echo "$json" | bash "$HOOK" 2>/dev/null || true
}

expect_blocked() {
  local label="$1"
  local command="$2"
  local output
  output=$(run_hook "$command")
  if echo "$output" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null 2>&1; then
    echo "✅ PASS: $label"
    ((PASS++))
  else
    echo "❌ FAIL: $label — expected deny, got: $output"
    ((FAIL++))
  fi
}

expect_allowed() {
  local label="$1"
  local command="$2"
  local output
  output=$(run_hook "$command")
  if [ -z "$output" ]; then
    echo "✅ PASS: $label"
    ((PASS++))
  else
    echo "❌ FAIL: $label — expected allow (empty output), got: $output"
    ((FAIL++))
  fi
}

echo "=== Testing block-destructive.sh ==="
echo ""

# --- Blocked commands ---
echo "--- Should BLOCK ---"
expect_blocked "rm -rf /"               "rm -rf /"
expect_blocked "rm -rf /tmp/build"      "rm -rf /tmp/build"
expect_blocked "rm -fr /home"           "rm -fr /home"
expect_blocked "rm -r -f dir"           "rm -r -f dir"
expect_blocked "rm -f -r dir"           "rm -f -r dir"
expect_blocked "sudo rm -rf /"          "sudo rm -rf /"
expect_blocked "DROP TABLE users"       "mysql -e 'DROP TABLE users'"
expect_blocked "drop table (lowercase)" "psql -c 'drop table users'"
expect_blocked "git push --force"       "git push --force origin main"
expect_blocked "git push -f"            "git push -f origin main"
expect_blocked "TRUNCATE users"         "mysql -e 'TRUNCATE users'"
expect_blocked "truncate (lowercase)"   "psql -c 'truncate table users'"
expect_blocked "DELETE FROM no WHERE"   "mysql -e 'DELETE FROM users'"

# --- Allowed commands ---
echo ""
echo "--- Should ALLOW ---"
expect_allowed "rm single file"         "rm file.txt"
expect_allowed "rm -r (no -f)"          "rm -r dir/"
expect_allowed "rm -f (no -r)"          "rm -f file.txt"
expect_allowed "git push (normal)"      "git push origin main"
expect_allowed "git push --force-with-lease" "git push --force-with-lease origin main"
expect_allowed "DELETE FROM with WHERE" "mysql -e 'DELETE FROM users WHERE id=1'"
expect_allowed "ls -la"                 "ls -la"
expect_allowed "npm test"               "npm test"
expect_allowed "echo hello"             "echo hello"
expect_allowed "grep -r pattern ."      "grep -r pattern ."

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
