#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$ROOT/hook.sh"
chmod +x "$HOOK"

run_hook() {
  local cmd="$1"
  python3 - "$cmd" <<'PY' | "$HOOK" 2>/dev/null || true
import json, sys
cmd = sys.argv[1]
print(json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": "/tmp/proj"}))
PY
}

expect_block() {
  local cmd="$1"
  local out
  out="$(run_hook "$cmd")"
  if [[ "$out" != *'"decision":"block"'* ]]; then
    echo "FAIL expected block: $cmd"
    echo "  got: $out"
    exit 1
  fi
  echo "PASS [blocked] $cmd"
}

expect_allow() {
  local cmd="$1"
  local out
  out="$(run_hook "$cmd")"
  if [[ -n "$out" ]]; then
    echo "FAIL expected allow: $cmd"
    echo "  got: $out"
    exit 1
  fi
  echo "PASS [allowed] $cmd"
}

echo "=== Dangerous ==="
expect_block 'rm -rf /tmp/x'
expect_block 'rm -fr ./build'
expect_block 'rm --force --recursive /tmp/x'
expect_block 'rm --recursive --force ./build'
expect_block 'DROP TABLE users'
expect_block 'drop table users'
expect_block 'TRUNCATE logs'
expect_block 'DELETE FROM users'
expect_block 'git push --force origin main'
expect_block 'git push -f'
expect_block 'chmod -R 777 /'
expect_block 'echo "ok"; rm -rf /tmp/x'

echo "=== Safe ==="
expect_allow 'ls -la'
expect_allow 'npm install'
expect_allow 'git push origin main'
expect_allow 'DELETE FROM users WHERE id=1'
expect_allow 'rm ./single-file.txt'

echo "All tests passed."
