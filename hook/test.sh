#!/usr/bin/env bash
#
# test.sh — self-test for block-destructive.sh
#
# Pipes sample Claude Code PreToolUse JSON payloads through the hook via
# stdin and asserts the expected block/allow verdict for each.
# Uses a throwaway HOME so the hook's log never touches the real ~/.claude.
#
# Usage: bash test.sh   (from anywhere; finds the hook next to itself)

set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
HOOK="$HERE/block-destructive.sh"

[ -f "$HOOK" ] || { echo "hook not found: $HOOK" >&2; exit 1; }

# Isolated HOME for the hook's blocked.log
TEST_HOME="$(mktemp -d "${TMPDIR:-/tmp}/hooktest.XXXXXX")"
export HOME="$TEST_HOME"
trap 'rm -rf "$TEST_HOME"' EXIT

pass=0
fail=0
expected_blocks=0

# run_case <block|allow> <command> [label]
run_case() {
  local expected=$1 command=$2 label=${3:-$2}
  # Escape the command for embedding in a JSON string
  local esc=${command//\\/\\\\}
  esc=${esc//\"/\\\"}
  local payload
  payload=$(printf '{"session_id":"test","tool_name":"Bash","tool_input":{"command":"%s"},"cwd":"/tmp/proj"}' "$esc")
  local out rc
  out="$(printf '%s' "$payload" | bash "$HOOK" 2>&1)"
  rc=$?
  local ok=0
  if [ "$expected" = "block" ]; then
    expected_blocks=$((expected_blocks + 1))
    if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q '"decision":"block"'; then ok=1; fi
  else
    if [ "$rc" -eq 0 ]; then ok=1; fi
  fi
  if [ "$ok" -eq 1 ]; then
    pass=$((pass + 1))
    printf 'PASS  [%s]  %s\n' "$expected" "$label"
  else
    fail=$((fail + 1))
    printf 'FAIL  [%s]  %s  (rc=%s, output: %s)\n' "$expected" "$label" "$rc" "$out"
  fi
}

echo "== block cases =="
run_case block 'rm -rf /'
run_case block 'rm -fr ./build'
run_case block 'rm -r -f /tmp/data'
run_case block 'rm --recursive --force /var/data'
run_case block 'echo "hi" && rm -rf /var/log'
run_case block 'DROP TABLE users'
run_case block 'drop table if exists users'
run_case block 'git push --force origin main'
run_case block 'git push -f origin main'
run_case block 'TRUNCATE TABLE sessions'
run_case block 'truncate users'
run_case block 'DELETE FROM users'
run_case block 'DELETE FROM orders LIMIT 5'

echo "== allow cases =="
run_case allow 'ls -la'
run_case allow 'rm file.txt'
run_case allow 'git push origin main'
run_case allow 'git push -u origin main'
run_case allow 'DELETE FROM users WHERE id=1'
run_case allow 'npm run build'
run_case allow 'echo "TRUNCATE is a word"'
run_case allow 'echo "DROP TABLE users"'
run_case allow 'echo "rm -rf is scary"'
run_case allow 'git -c user.name=x push origin main'

echo "== log check =="
LOG_FILE="$TEST_HOME/.claude/hooks/blocked.log"
if [ -f "$LOG_FILE" ]; then
  lines=$(wc -l < "$LOG_FILE")
  if [ "$lines" -eq "$expected_blocks" ]; then
    pass=$((pass + 1))
    printf 'PASS  [log]   blocked.log has %s line(s), one per blocked attempt\n' "$lines"
  else
    fail=$((fail + 1))
    printf 'FAIL  [log]   blocked.log has %s line(s), expected %s\n' "$lines" "$expected_blocks"
  fi
else
  fail=$((fail + 1))
  printf 'FAIL  [log]   blocked.log not created at %s\n' "$LOG_FILE"
fi

echo
echo "Total: $((pass + fail))  Passed: $pass  Failed: $fail"
[ "$fail" -eq 0 ]
