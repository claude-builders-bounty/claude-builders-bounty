#!/usr/bin/env bash
# Test suite for pre-tool-use hook
set -uo pipefail

HOOK="$(dirname "$0")/pre-tool-use"
PASS=0
FAIL=0

run_test() {
  local description="$1"
  local tool_name="$2"
  local command="$3"
  local expect_blocked="$4"

  local input
  input=$(python3 -c "
import json, sys
print(json.dumps({
    'tool_name': sys.argv[1],
    'tool_params': {'command': sys.argv[2]},
    'project_path': '/tmp/test-project'
}))
" "$tool_name" "$command")

  local output=""
  local exit_code=0
  output=$(echo "$input" | bash "$HOOK" 2>&1) || exit_code=$?

  if [[ "$expect_blocked" == "yes" && "$exit_code" -eq 2 ]]; then
    echo "  ✅ PASS: $description"
    ((PASS++))
  elif [[ "$expect_blocked" == "no" && "$exit_code" -eq 0 ]]; then
    echo "  ✅ PASS: $description"
    ((PASS++))
  else
    echo "  ❌ FAIL: $description (exit=$exit_code, expected_blocked=$expect_blocked)"
    echo "    output: $output"
    ((FAIL++))
  fi
}

echo "=== Pre-Tool-Use Hook Test Suite ==="
echo ""

echo "--- Destructive commands (should be BLOCKED) ---"
run_test "rm -rf /"                   "Bash" "rm -rf /"                          "yes"
run_test "rm -rf with path"           "Bash" "rm -rf /var/data"                  "yes"
run_test "rm -fr variant"             "Bash" "rm -fr ./build"                    "yes"
run_test "DROP TABLE"                 "Bash" "psql -c 'DROP TABLE users'"        "yes"
run_test "drop table lowercase"       "Bash" "mysql -e 'drop table orders'"      "yes"
run_test "git push --force"           "Bash" "git push --force origin main"      "yes"
run_test "git push -f"                "Bash" "git push -f origin main"           "yes"
run_test "TRUNCATE TABLE"             "Bash" "psql -c 'TRUNCATE TABLE sessions'" "yes"
run_test "truncate lowercase"         "Bash" "mysql -e 'truncate table logs'"    "yes"
run_test "DELETE FROM without WHERE"  "Bash" "psql -c 'DELETE FROM users'"       "yes"

echo ""
echo "--- Safe commands (should be ALLOWED) ---"
run_test "normal rm (single file)"    "Bash" "rm file.txt"                       "no"
run_test "ls command"                 "Bash" "ls -la"                            "no"
run_test "echo command"               "Bash" "echo hello"                        "no"
run_test "npm install"                "Bash" "npm install express"               "no"
run_test "git push (no force)"        "Bash" "git push origin main"              "no"
run_test "git commit"                 "Bash" "git commit -m fix"                 "no"
run_test "DELETE with WHERE"          "Bash" "psql -c 'DELETE FROM users WHERE id=5'" "no"
run_test "Non-Bash tool ignored"      "Read" "rm -rf /"                          "no"
run_test "cat command"                "Bash" "cat README.md"                     "no"
run_test "grep command"               "Bash" "grep -r TODO ."                    "no"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
