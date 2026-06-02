#!/usr/bin/env bash
set -uo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"

deny() {
  jq -n --arg r "$1" \
    '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$r}}'
  exit 0
}

if ! command -v jq &>/dev/null; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[HOOK ERROR] jq is not installed."}}\n'
  exit 0
fi

INPUT=$(cat)

if [[ -z "$INPUT" ]]; then
  deny "[HOOK ERROR] Received empty input; cannot verify command safety."
fi

_parsed=$(printf '%s' "$INPUT" | jq -r '
  @sh "TOOL_NAME=\(.tool_name // "")",
  @sh "CWD=\(.cwd // "unknown")",
  @sh "COMMAND=\(.tool_input.command // "")"
' 2>/dev/null) || deny "[HOOK ERROR] Failed to parse hook input JSON."
[[ -z "$_parsed" ]] && deny "[HOOK ERROR] Failed to parse hook input JSON."
eval "$_parsed"

if [[ "$TOOL_NAME" != "Bash" ]]; then
  exit 0
fi

if [[ -z "$COMMAND" ]]; then
  deny "[HOOK ERROR] Bash tool detected but .tool_input.command is missing."
fi

CMD_LOWER=$(printf '%s' "$COMMAND" | tr '[:upper:]' '[:lower:]')

block() {
  local reason="$1"
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s\t%s\t%s\t%s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$COMMAND" "$CWD" "$reason" >> "$LOG_FILE"
  deny "[BLOCKED] $reason. Use a safer alternative or ask the user for confirmation."
}

m() { [[ "$CMD_LOWER" =~ $1 ]]; }

# rm with both recursive and force flags
if m '(^|[;&|]|sudo |xargs |exec |env )rm ' || m 'find .*rm '; then
  if m ' -[a-z]*r[a-z]*f| -[a-z]*f[a-z]*r'; then
    block "Destructive file removal (rm -rf)"
  fi
  if m ' (-r|--recursive)( |$)' && m ' (-f|--force)( |$)'; then
    block "Destructive file removal (rm -rf)"
  fi
fi

# git push --force (excludes --force-with-lease and --force-if-includes)
if m 'git +push '; then
  if m ' --force( |$)| -f( |$)'; then
    if ! m ' --force-with-lease| --force-if-includes'; then
      block "Force push (git push --force)"
    fi
  fi
fi

if m 'git +reset +--hard'; then
  block "Destructive git operation (git reset --hard discards all uncommitted changes)"
fi

if m 'git +clean +-[a-z]*f[a-z]*d|git +clean +-[a-z]*d[a-z]*f'; then
  block "Destructive git operation (git clean -fd removes untracked files and directories)"
fi

if m 'drop +table'; then
  block "Destructive SQL (DROP TABLE)"
fi

if m 'truncate '; then
  block "Destructive SQL (TRUNCATE)"
fi

if m 'delete +from ' && ! m 'where'; then
  block "Destructive SQL (DELETE FROM without WHERE clause)"
fi

exit 0
