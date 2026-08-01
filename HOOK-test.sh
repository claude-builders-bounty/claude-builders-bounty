#!/usr/bin/env bash
# test.sh — unit tests for block-destructive-commands
# Usage: bash test.sh

set -uo pipefail

HOOK_WIN="$(cygpath -w "$(cd "$(dirname "$0")" && pwd)")\\block-destructive-commands.py"
HOOK="block-destructive-commands.py"  # relative to test dir, run from there

# Detect python command (python3 on Windows is often a broken stub)
if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" 2>/dev/null && [[ "$(python3 -c 'import sys; print(sys.executable)' 2>/dev/null)" != *WindowsApps* ]]; then
  PY=python3
elif command -v python >/dev/null 2>&1 && python -c "import sys" 2>/dev/null; then
  PY=python
else
  echo "ERROR: working Python not found" >&2
  exit 1
fi

PASS=0
FAIL=0
FAILED_TESTS=()

# Test a command. Args: expected_decision (block|allow) description command
assert() {
  local expected="$1"
  local desc="$2"
  local cmd="$3"
  # Build JSON input via python
  local input
  input="$($PY -c "import json,sys; print(json.dumps({'tool_input':{'command':sys.argv[1]},'cwd':'/tmp/test'}))" "$cmd")"
  local result
  result="$(printf '%s' "$input" | $PY "$HOOK_WIN" 2>&1)"
  if echo "$result" | grep -q "\"decision\": \"$expected\""; then
    PASS=$((PASS + 1))
    echo "  ✅ $expected: $desc"
  else
    FAIL=$((FAIL + 1))
    FAILED_TESTS+=("$desc (cmd: $cmd)")
    echo "  ❌ expected $expected, got: $desc"
    echo "     cmd:    $cmd"
    echo "     result: ${result:0:200}"
  fi
}

echo "=== Tests for block-destructive-commands ==="
echo ""
echo "--- Should be BLOCKED ---"
assert block "rm -rf"                          "rm -rf node_modules"
assert block "rm -rf /"                        "sudo rm -rf /"
assert block "rm --recursive --force"          "rm --recursive --force build"
assert block "DROP TABLE"                      'psql -c "DROP TABLE users"'
assert block "TRUNCATE with TABLE"             'psql -c "TRUNCATE TABLE logs"'
assert block "TRUNCATE without TABLE"          'psql -c "TRUNCATE logs"'
assert block "DELETE FROM no WHERE"            'psql -c "DELETE FROM sessions"'
assert block "DELETE FROM no WHERE with ;"     'psql -c "DELETE FROM sessions;"'
assert block "git push --force"                "git push --force origin main"
assert block "git push -f"                     "git push -f"
assert block "git push --force-with-lease"     "git push --force-with-lease"

echo ""
echo "--- Should be ALLOWED ---"
assert allow "rm single file"                  "rm file.txt"
assert allow "rm with no flags"                "rm -v file.txt"
assert allow "rm -i (interactive)"             "rm -i file.txt"
assert allow "DELETE FROM with WHERE"          'psql -c "DELETE FROM sessions WHERE id = 5"'
assert allow "git push normal"                 "git push origin main"
assert allow "git push --no-verify"            "git push --no-verify origin main"
assert allow "DROP DATABASE (not in spec)"     'psql -c "DROP DATABASE test"'
assert allow "DROP INDEX (not in spec)"        'psql -c "DROP INDEX idx_users"'
assert allow "ls -la"                          "ls -la"
assert allow "echo hello"                      'echo "hello"'
assert allow "empty command"                   ""

echo ""
echo "=== Summary ==="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"

if [[ $FAIL -gt 0 ]]; then
  echo ""
  echo "  Failed tests:"
  for t in "${FAILED_TESTS[@]}"; do
    echo "    - $t"
  done
  exit 1
fi

echo ""
echo "  ✅ All tests pass."
