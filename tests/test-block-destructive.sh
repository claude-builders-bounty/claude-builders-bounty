#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="${ROOT}/hooks/block-destructive.sh"
PASS=0
FAIL=0

chmod +x "$HOOK"

assert_blocked() {
  local name=$1
  local payload=$2
  local out
  out=$(echo "$payload" | "$HOOK")
  if echo "$out" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null; then
    PASS=$((PASS + 1))
    echo "PASS: $name"
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $name (expected deny)"
    echo "  output: $out"
  fi
}

assert_allowed() {
  local name=$1
  local payload=$2
  local out
  out=$(echo "$payload" | "$HOOK" || true)
  if [[ -z "$out" ]]; then
    PASS=$((PASS + 1))
    echo "PASS: $name"
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $name (expected allow)"
    echo "  output: $out"
  fi
}

assert_blocked "rm -rf" \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf ./dist"},"cwd":"/tmp/proj"}'

assert_blocked "rm --recursive --force" \
  '{"tool_name":"Bash","tool_input":{"command":"rm --recursive --force build"},"cwd":"/tmp/proj"}'

assert_blocked "DROP TABLE" \
  '{"tool_name":"Bash","tool_input":{"command":"psql -c \"DROP TABLE users;\""},"cwd":"/tmp/proj"}'

assert_blocked "git push --force" \
  '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"},"cwd":"/tmp/proj"}'

assert_blocked "git push -f" \
  '{"tool_name":"Bash","tool_input":{"command":"git push -f origin main"},"cwd":"/tmp/proj"}'

assert_blocked "TRUNCATE" \
  '{"tool_name":"Bash","tool_input":{"command":"TRUNCATE TABLE logs;"},"cwd":"/tmp/proj"}'

assert_blocked "DELETE FROM no WHERE" \
  '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM sessions;"},"cwd":"/tmp/proj"}'

assert_blocked "DELETE FROM in compound" \
  '{"tool_name":"Bash","tool_input":{"command":"SELECT 1; DELETE FROM users; SELECT 2;"},"cwd":"/tmp/proj"}'

assert_allowed "rm single file" \
  '{"tool_name":"Bash","tool_input":{"command":"rm file.txt"},"cwd":"/tmp/proj"}'

assert_allowed "git push normal" \
  '{"tool_name":"Bash","tool_input":{"command":"git push origin main"},"cwd":"/tmp/proj"}'

assert_allowed "git push force-with-lease" \
  '{"tool_name":"Bash","tool_input":{"command":"git push --force-with-lease origin main"},"cwd":"/tmp/proj"}'

assert_allowed "DELETE FROM with WHERE" \
  '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM sessions WHERE expired = true;"},"cwd":"/tmp/proj"}'

assert_allowed "non-Bash tool" \
  '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/x"},"cwd":"/tmp/proj"}'

assert_allowed "ls normal" \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp/proj"}'

TEST_HOME="${TMPDIR:-/tmp}/bounty3-test-$$"
mkdir -p "$TEST_HOME/.claude/hooks"
cp "$HOOK" "$TEST_HOME/.claude/hooks/block-destructive.sh"
chmod +x "$TEST_HOME/.claude/hooks/block-destructive.sh"
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/work/proj"}' \
  | HOME="$TEST_HOME" "$TEST_HOME/.claude/hooks/block-destructive.sh" >/dev/null
if [[ -f "$TEST_HOME/.claude/hooks/blocked.log" ]] \
  && jq -e '.command == "rm -rf /" and .project_path == "/work/proj"' \
    "$TEST_HOME/.claude/hooks/blocked.log" >/dev/null; then
  PASS=$((PASS + 1))
  echo "PASS: blocked.log written"
else
  FAIL=$((FAIL + 1))
  echo "FAIL: blocked.log not written correctly"
fi
rm -rf "$TEST_HOME"

echo "---"
echo "$PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
