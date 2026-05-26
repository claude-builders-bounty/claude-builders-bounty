#!/usr/bin/env bash
# Claude Code PreToolUse hook — block destructive Bash before execution.
# bash 3.2+; JSON parsed with python3 when available.
set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

payload="$(cat)"

tool_name=""
command=""
cwd=""

if command -v python3 >/dev/null 2>&1; then
  _parsed="$(printf '%s' "$payload" | python3 -c '
import json, sys
d = json.load(sys.stdin)
ti = d.get("tool_input")
if not isinstance(ti, dict):
    ti = {}
cmd = ti.get("command", d.get("command", ""))
if not isinstance(cmd, str):
    cmd = ""
fields = [d.get("tool_name", ""), cmd, d.get("cwd", "")]
print("\x1e".join(fields))
')"
  IFS=$'\x1e' read -r tool_name command cwd <<EOF
$_parsed
EOF
else
  tool_name="$(printf '%s' "$payload" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
  command="$(printf '%s' "$payload" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
  cwd="$(printf '%s' "$payload" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
fi

if [[ "$tool_name" != "Bash" ]] || [[ -z "$command" ]]; then
  exit 0
fi

lower="$(printf '%s' "$command" | tr '[:upper:]' '[:lower:]')"

block_reason=""

case "$lower" in
  *"rm -rf"*|*"rm -fr"*|*"rm -r -f"*|*"rm -f -r"*)
    block_reason="recursive force delete (rm -rf)" ;;
  *"rm --recursive"*"--force"*|*"rm --force"*"--recursive"*)
    block_reason="recursive force delete (rm -rf)" ;;
  *"drop table"*|*"drop database"*)
    block_reason="DROP TABLE/DATABASE" ;;
  *"truncate "*)
    block_reason="TRUNCATE" ;;
  *"git push"*"--force"*|*"git push -f"*|*"git push"*" -f"*)
    block_reason="git push --force" ;;
  mkfs*|*"dd "*"of=/dev/"*|*">/dev/sd"*|*"> /dev/sd"*)
    block_reason="disk format / raw device write" ;;
  *"chmod -r 777 /"*|*"chmod -r 777  /"*)
    block_reason="chmod -R 777 /" ;;
esac

if [[ -z "$block_reason" ]] && [[ "$lower" == *"delete from"* ]] && [[ "$lower" != *" where "* ]]; then
  block_reason="DELETE without WHERE"
fi

if [[ -z "$block_reason" ]]; then
  exit 0
fi

ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
printf '%s BLOCKED [%s] cwd=%s cmd=%s\n' "$ts" "$block_reason" "$cwd" "$command" >>"$LOG_FILE"

escaped_cmd="$(printf '%s' "$command" | sed 's/\\/\\\\/g; s/"/\\"/g')"
printf '{"decision":"block","reason":"Blocked destructive Bash: %s. Command: %s"}\n' "$block_reason" "$escaped_cmd"
exit 0
