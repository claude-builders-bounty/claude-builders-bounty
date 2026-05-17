#!/usr/bin/env bash
# Claude Code pre-tool-use hook (bash version) — blocks dangerous commands.
# Place at: ~/.claude/hooks/pre_tool_use
# Requires: jq

LOG_FILE="$HOME/.claude/hooks/blocked.log"
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Only intercept Bash tool
if [ "$TOOL_NAME" != "Bash" ] || [ -z "$COMMAND" ]; then
    echo '{"continue":true}'
    exit 0
fi

# Check against dangerous patterns
REASON=""
if echo "$COMMAND" | grep -qiE 'rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)'; then
    REASON="rm -rf (recursive force delete)"
elif echo "$COMMAND" | grep -qiE 'DROP\s+TABLE'; then
    REASON="DROP TABLE (database table destruction)"
elif echo "$COMMAND" | grep -qiE 'git\s+push\s+.*(--force|-[^-]*f)'; then
    REASON="git push --force (force push)"
elif echo "$COMMAND" | grep -qiE 'TRUNCATE\s+'; then
    REASON="TRUNCATE (table data deletion)"
elif echo "$COMMAND" | grep -qiE 'DELETE\s+FROM' && ! echo "$COMMAND" | grep -qi 'WHERE'; then
    REASON="DELETE FROM without WHERE (full table wipe)"
fi

if [ -n "$REASON" ]; then
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date -Iseconds)] reason=$REASON project=$(pwd) command=$(echo "$COMMAND" | jq -Rs .)" >> "$LOG_FILE"

    MSG="🚫 BLOCKED — $REASON

The following command was intercepted:
  $COMMAND

This command is dangerous and has been blocked by the safety hook.
Logged to: $LOG_FILE"

    echo "{\"continue\":false,\"reason\":$(echo "$MSG" | jq -Rs .)}"
    exit 0
fi

# Safe — allow
echo '{"continue":true}'
