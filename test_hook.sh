#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$ROOT/hooks/block-destructive-bash.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
run_hook() { printf '%s' "$1" | CLAUDE_HOOK_LOG="$TMP/blocked.log" "$HOOK"; }
set +e
run_hook '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"}}' >"$TMP/out" 2>"$TMP/err"
status=$?
set -e
test "$status" -eq 2
grep -q 'blocked' "$TMP/err"
grep -q 'rm -rf /tmp/demo' "$TMP/blocked.log"
set +e
run_hook '{"tool_name":"Bash","tool_input":{"command":"echo hello"}}' >"$TMP/out" 2>"$TMP/err"
status=$?
set -e
test "$status" -eq 0
set +e
run_hook '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users"}}' >"$TMP/out" 2>"$TMP/err"
status=$?
set -e
test "$status" -eq 2
echo "all hook tests passed"
