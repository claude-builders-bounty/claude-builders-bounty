#!/usr/bin/env bash
set -euo pipefail
LOG="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG")"
payload="$(cat)"
cmd="$(echo "$payload" | jq -r '.tool_input.command // .command // empty' 2>/dev/null || true)"
cwd="$(echo "$payload" | jq -r '.cwd // .workspace // empty' 2>/dev/null || pwd)"
block(){ local r="$1" t="$(date -u +%FT%TZ)"
  printf '%s | cwd=%s | cmd=%s | %s\n' "$t" "$cwd" "$cmd" "$r" >>"$LOG"
  jq -n --arg m "BLOCKED: $r ($cmd)" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$m}}'; exit 0; }
[ -z "$cmd" ] && exit 0
echo "$cmd" | grep -qE 'rm -rf[[:space:]]+(/tmp|node_modules|build/?|dist/?|__pycache__)' && exit 0
echo "$cmd" | grep -qiE 'rm[[:space:]]+-rf' && block "rm -rf blocked"
echo "$cmd" | grep -qiE 'DROP[[:space:]]+(TABLE|DATABASE)' && block "DROP blocked"
echo "$cmd" | grep -qiE 'TRUNCATE[[:space:]]+TABLE' && block "TRUNCATE blocked"
echo "$cmd" | grep -qiE 'DELETE[[:space:]]+FROM' && ! echo "$cmd" | grep -qi WHERE && block "DELETE without WHERE"
echo "$cmd" | grep -qiE 'git[[:space:]]+push.*(-f|--force)' && block "force push blocked"
exit 0
