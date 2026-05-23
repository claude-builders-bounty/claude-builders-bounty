#!/usr/bin/env bash
set -euo pipefail
HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/pre-tool-use-block.py"

run_case () {
  name="$1"; payload="$2"
  echo "== $name =="
  set +e
  out=$(printf '%s' "$payload" | "$HOOK" 2>&1)
  code=$?
  set -e
  echo "exit=$code"
  echo "$out"
  echo
}

run_case "allow normal" '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp/demo"}'
run_case "block rm -rf" '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp/demo"}'
run_case "block delete no where" '{"tool_name":"Bash","tool_input":{"command":"sqlite3 app.db \"DELETE FROM users;\""},"cwd":"/tmp/demo"}'
