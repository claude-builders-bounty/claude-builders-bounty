#!/usr/bin/env bash
#
# pre-bash-hook.sh — PreToolUse hook that blocks destructive bash commands
#
# Input:  JSON on stdin with .tool_input.command
# Output: exit 0 = allow, exit 2 = block (stderr = reason to Claude)
# Log:    ~/.claude/hooks/blocked.log
#

set -euo pipefail

# --- Read input ---
stdin=""
if [ -t 0 ]; then
  stdin="{}"
else
  stdin=$(cat)
fi

# Extract fields
if command -v jq &>/dev/null; then
  CMD=$(echo "$stdin" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")
elif command -v python3 &>/dev/null; then
  CMD=$(echo "$stdin" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
else
  CMD=""
fi

CWD=$(echo "$stdin" | jq -r '.cwd // "unknown"' 2>/dev/null || echo "unknown")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -Iseconds 2>/dev/null || echo "unknown")

# --- Block check ---
BLOCKED=0
REASON=""

# 1. rm -rf with dangerous targets
if echo "$CMD" | grep -Eiq 'rm\s+(-rf|-r\s+-f|-f\s+-r)\s+(/\s*$|/\S+|\s+--no-preserve=root)'; then
  BLOCKED=1
  REASON="rm -rf can permanently delete files/directories. Use 'rm' with explicit file lists instead, or confirm with 'ls' first."
fi

# 2. DROP TABLE (but allow DROP TABLE IF EXISTS)
if [ "$BLOCKED" = "0" ] && echo "$CMD" | grep -Eiq 'DROP\s+TABLE\b'; then
  if ! echo "$CMD" | grep -Eiq 'DROP\s+TABLE\s+IF\s+EXISTS'; then
    BLOCKED=1
    REASON="DROP TABLE permanently destroys database data. Use a migration rollback or CREATE TABLE AS SELECT instead."
  fi
fi

# 3. git push --force (but allow --force-with-lease)
if [ "$BLOCKED" = "0" ] && echo "$CMD" | grep -Eiq 'git\s+push\s+--force\b'; then
  if ! echo "$CMD" | grep -Eiq 'force-with-lease'; then
    BLOCKED=1
    REASON="git push --force rewrites remote history. Use 'git push --force-with-lease' instead, or confirm you understand the risk."
  fi
fi

if [ "$BLOCKED" = "0" ] && echo "$CMD" | grep -Eiq 'git\s+push\s+-f\b'; then
  if ! echo "$CMD" | grep -Eiq 'force-with-lease'; then
    BLOCKED=1
    REASON="git push --force rewrites remote history. Use 'git push --force-with-lease' instead, or confirm you understand the risk."
  fi
fi

# 4. TRUNCATE TABLE
if [ "$BLOCKED" = "0" ] && echo "$CMD" | grep -Eiq 'TRUNCATE\s+TABLE'; then
  BLOCKED=1
  REASON="TRUNCATE TABLE permanently removes all rows. Use 'DELETE FROM <table> WHERE <condition>' to selectively remove data."
fi

# 5. DELETE FROM without WHERE
if [ "$BLOCKED" = "0" ] && echo "$CMD" | grep -Eiq 'DELETE\s+FROM\b'; then
  if ! echo "$CMD" | grep -Eiq 'WHERE'; then
    BLOCKED=1
    REASON="DELETE FROM without WHERE removes ALL rows. Add a WHERE clause or use 'SELECT COUNT(*)' first to verify the scope."
  fi
fi

# --- Act ---
if [ "$BLOCKED" = "1" ]; then
  LOG_LINE="[${TIMESTAMP}] BLOCKED: '${CMD}' [cwd: ${CWD}]"
  mkdir -p ~/.claude/hooks
  echo "$LOG_LINE" >> ~/.claude/hooks/blocked.log
  echo "$REASON" >&2
  exit 2
fi

exit 0
