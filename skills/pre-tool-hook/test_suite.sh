#!/usr/bin/env bash
# Test suite for pre_tool_use_hook.py
# Verifies blocking behavior for destructive commands

set +e  # We handle errors manually

HOOK_PATH="$(dirname "$(realpath "$0")")/pre_tool_use_hook.py"

# Test cases: (command, expected_exit_code)
declare -a tests=(
  "rm -rf /tmp/test:1"
  "git push --force origin main:1"
  "DROP TABLE users;:1"
  "TRUNCATE TABLE logs;:1"
  "DELETE FROM users;:1"
  "DELETE FROM users WHERE id=1:0"
  "SELECT * FROM users;:0"
  "echo 'hello':0"
  "ls -la:0"
  "cat /etc/passwd:0"
  "git commit -m 'fix':0"
  "python script.py:0"
  "rm -r dir:0"  # -r without -f should pass
  "DROP TABLE IF EXISTS users;:1"  # still drops
  "truncate table test:1"
  "DELETE FROM t;:1"
)

passed=0
failed=0

echo "Testing hook at: $HOOK_PATH"
echo ""

for test in "${tests[@]}"; do
  IFS=':' read -r cmd expected <<< "$test"
  echo -n "Test: $cmd ... "
  
  # Build JSON payload
  payload="{\"tool\": \"bash\", \"input\": {\"command\": \"$cmd\"}}"
  
  # Run hook
  exit_code=0
  output=$(echo "$payload" | python3 "$HOOK_PATH" 2>/dev/null) || exit_code=$?
  
  if [ "$exit_code" -eq "$expected" ]; then
    echo "PASS"
    ((passed++))
  else
    echo "FAIL (expected $expected, got $exit_code)"
    echo "  Output: $output"
    ((failed++))
  fi
done

echo ""
echo "Results: $passed passed, $failed failed"
exit $failed
