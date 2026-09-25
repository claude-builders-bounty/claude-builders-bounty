#!/usr/bin/env bash
# Tests block_destructive.py against the acceptance criteria.
set -u
HOOK="${1:-./block_destructive.py}"
pass=0
fail=0

check() {
  # $1 = label, $2 = expected decision (block|allow), $3 = command
  local out
  out=$(printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$3" | python3 "$HOOK" 2>/dev/null)
  if printf '%s' "$out" | grep -q "\"decision\": \"$2\""; then
    echo "PASS: $1"
    pass=$((pass + 1))
  else
    echo "FAIL: $1 -> $out"
    fail=$((fail + 1))
  fi
}

check "blocks rm -rf" block "rm -rf /tmp/build"
check "blocks rm -fr" block "rm -fr /tmp/build"
check "blocks DROP TABLE" block "psql -c 'DROP TABLE users'"
check "blocks git push --force" block "git push origin main --force"
check "blocks git push -f" block "git push -f origin main"
check "blocks git push --force-with-lease" block "git push origin main --force-with-lease"
check "blocks TRUNCATE" block "TRUNCATE TABLE audit_log"
check "blocks DELETE without WHERE" block "DELETE FROM users"
check "allows DELETE with WHERE" allow "DELETE FROM users WHERE id = 1"
check "allows safe ls" allow "ls -la"
check "allows safe git status" allow "git status"
check "allows rm of a single file" allow "rm /tmp/one-file.txt"

echo "passed=$pass failed=$fail"
[ "$fail" -eq 0 ]
