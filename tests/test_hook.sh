#!/usr/bin/env bash
HOOK="../hooks/pre-tool-use"
fail=0; pass=0
test_cmd() {
  CLAUDE_TOOL_NAME="Bash" CLAUDE_INPUT="$1" bash "$HOOK" >/dev/null 2>&1
  if [ "$2" = "true" ] && [ $? -ne 0 ]; then echo "  OK: $1"; return 0
  elif [ "$2" = "false" ] && [ $? -eq 0 ]; then echo "  OK: $1"; return 0
  else echo "  FAIL: $1 (expect block=$2)"; return 1; fi
}
echo "=== Bash Hook Tests ==="
test_cmd "rm -rf /" true; test_cmd "DROP TABLE users" true
test_cmd "git push --force" true; test_cmd "git status" false
test_cmd "ls -la" false; test_cmd "npm install" false
test_cmd "rm file.txt" false
echo "Done"
