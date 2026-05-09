#!/usr/bin/env bash
set -euo pipefail

hook="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/pre-tool-use.py"

assert_decision() {
  local command="$1"
  local expected="$2"
  local actual

  actual="$(
    printf '%s' "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$command\"},\"cwd\":\"/tmp/project\"}" \
      | python3 "$hook" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"])'
  )"

  if [[ "$actual" != "$expected" ]]; then
    echo "expected '$command' to return '$expected', got '$actual'" >&2
    exit 1
  fi
}

python3 -m py_compile "$hook"

assert_decision "rm -rf build" "deny"
assert_decision "rm -fr build" "deny"
assert_decision "sudo rm --recursive --force build" "deny"
assert_decision "rm -r build" "allow"
assert_decision "DROP TABLE users" "deny"
assert_decision "git push --force origin main" "deny"
assert_decision "TRUNCATE users" "deny"
assert_decision "DELETE FROM users" "deny"
assert_decision "DELETE FROM users WHERE id = 1" "allow"
assert_decision "git status" "allow"

echo "pre-tool-use hook tests passed"
