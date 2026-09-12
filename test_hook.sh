#!/usr/bin/env bash
set -euo pipefail

hook="$(cd "$(dirname "$0")" && pwd)/.claude/hooks/block-destructive.sh"
log_dir="$(mktemp -d)"
trap 'rm -rf "$log_dir"' EXIT

export HOME="$log_dir"
export CLAUDE_PROJECT_DIR="/tmp/example-project"

json_command() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

run_hook() {
  local command="$1"
  printf '{"cwd":"/tmp/example-project","tool_input":{"command":%s}}' "$(json_command "$command")" | "$hook"
}

assert_blocks() {
  local output
  output="$(run_hook "$1")"
  python3 -c 'import json,sys; assert json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"] == "deny"' <<<"$output"
}

assert_allows() {
  local output
  output="$(run_hook "$1")"
  test -z "$output"
}

assert_blocks "rm -rf ./build"
assert_blocks "DROP TABLE users"
assert_blocks "git push --force origin main"
assert_blocks "TRUNCATE TABLE sessions"
assert_blocks "DELETE FROM users"
assert_allows "DELETE FROM users WHERE id = 1"
assert_allows "npm test"

test "$(wc -l < "$log_dir/.claude/hooks/blocked.log")" -eq 5
echo "hook tests passed"
