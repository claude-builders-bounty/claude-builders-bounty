#!/usr/bin/env bash
set -euo pipefail

HOOK="$(dirname "$0")/destructive_bash_guard.py"

should_block() {
  local name="$1"
  local payload="$2"
  if printf '%s' "$payload" | "$HOOK" >/tmp/hook_stdout 2>/tmp/hook_stderr; then
    echo "FAIL: $name should have been blocked"
    cat /tmp/hook_stdout /tmp/hook_stderr
    exit 1
  fi
  echo "PASS blocked: $name"
}

should_allow() {
  local name="$1"
  local payload="$2"
  if ! printf '%s' "$payload" | "$HOOK" >/tmp/hook_stdout 2>/tmp/hook_stderr; then
    echo "FAIL: $name should have been allowed"
    cat /tmp/hook_stdout /tmp/hook_stderr
    exit 1
  fi
  echo "PASS allowed: $name"
}

should_block "rm -rf" '{"tool_input":{"command":"rm -rf /tmp/demo"}}'
should_block "DROP TABLE" '{"tool_input":{"command":"psql -c \"DROP TABLE users\""}}'
should_block "git push --force" '{"tool_input":{"command":"git push --force origin main"}}'
should_block "TRUNCATE" '{"tool_input":{"command":"TRUNCATE audit_logs"}}'
should_block "DELETE FROM without WHERE" '{"tool_input":{"command":"DELETE FROM users"}}'

should_allow "echo" '{"tool_input":{"command":"echo safe"}}'
should_allow "DELETE FROM with WHERE" '{"tool_input":{"command":"DELETE FROM users WHERE id = 1"}}'
should_allow "normal git push" '{"tool_input":{"command":"git push origin main"}}'
