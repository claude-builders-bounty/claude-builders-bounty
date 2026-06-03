#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$ROOT_DIR/hooks/block-dangerous-bash.sh"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s' "$value"
}

run_hook() {
  local command="$1"
  local tool_name="${2:-Bash}"
  local home="$TMP_DIR/home"

  rm -rf "$home"
  mkdir -p "$home"

  local escaped_command
  escaped_command="$(json_escape "$command")"

  HOME="$home" bash "$HOOK" <<JSON
{"hook_event_name":"PreToolUse","tool_name":"$tool_name","tool_input":{"command":"$escaped_command"},"cwd":"/tmp/example-project"}
JSON
}

assert_contains() {
  local value="$1"
  local expected="$2"

  if [[ "$value" != *"$expected"* ]]; then
    echo "Expected to find: $expected"
    echo "--- value ---"
    printf '%s\n' "$value"
    exit 1
  fi
}

assert_not_contains() {
  local value="$1"
  local unexpected="$2"

  if [[ "$value" == *"$unexpected"* ]]; then
    echo "Did not expect to find: $unexpected"
    echo "--- value ---"
    printf '%s\n' "$value"
    exit 1
  fi
}

assert_denied() {
  local command="$1"
  local reason="$2"
  local output
  output="$(run_hook "$command")"
  local log_file="$TMP_DIR/home/.claude/hooks/blocked.log"
  local log_text
  log_text="$(cat "$log_file")"

  assert_contains "$output" '"hookEventName":"PreToolUse"'
  assert_contains "$output" '"permissionDecision":"deny"'
  assert_contains "$output" "$reason"
  assert_contains "$log_text" "$command"
  assert_contains "$log_text" "/tmp/example-project"
}

assert_allowed() {
  local command="$1"
  local tool_name="${2:-Bash}"
  local output
  output="$(run_hook "$command" "$tool_name")"

  if [[ -n "$output" ]]; then
    echo "Safe command should not write hook output"
    printf '%s\n' "$output"
    exit 1
  fi
  if [[ -e "$TMP_DIR/home/.claude/hooks/blocked.log" ]]; then
    echo "Safe command should not create blocked.log"
    cat "$TMP_DIR/home/.claude/hooks/blocked.log"
    exit 1
  fi
}

assert_denied "rm -rf build" "rm -rf"
assert_denied "git push --force origin main" "git push --force"
assert_denied "psql -c 'DROP TABLE users'" "DROP TABLE"
assert_denied "mysql -e 'TRUNCATE sessions'" "TRUNCATE"
assert_denied "psql -c 'DELETE FROM users'" "DELETE FROM without WHERE"

assert_allowed "psql -c 'DELETE FROM users WHERE id = 1'"
assert_allowed "git status --short"
assert_allowed "rm -rf build" "Read"

echo "All hook tests passed."
