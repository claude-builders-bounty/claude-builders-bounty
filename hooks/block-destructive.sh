#!/usr/bin/env bash
# block-destructive.sh — Claude Code PreToolUse hook
# Blocks destructive bash commands before they execute.
#
# Blocked patterns:
#   rm -rf / rm -fr (recursive force delete)
#   DROP TABLE (SQL)
#   git push --force / git push -f
#   TRUNCATE (SQL)
#   DELETE FROM without WHERE clause (SQL)
#
# Logs blocked attempts to ~/.claude/hooks/blocked.log

set -euo pipefail

INPUT=$(cat)

# Extract command from tool_input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // .tool_input.input // empty' 2>/dev/null || true)

# If we can't parse the command, allow it (fail open — don't break normal workflow)
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

UPPER=$(echo "$COMMAND" | tr '[:lower:]' '[:upper:]')
LOG_DIR="$HOME/.claude/hooks"
LOG_FILE="$LOG_DIR/blocked.log"

mkdir -p "$LOG_DIR"

# ── Pattern checks ──────────────────────────────────────────────────────
BLOCKED=false
REASON=""

# rm -rf / rm -fr — check for 'rm' with flags containing BOTH r and f
if echo "$UPPER" | grep -qE '^RM\s+-|[^a-zA-Z]RM\s+-'; then
  FLAGS=$(echo "$UPPER" | grep -oE '\s+-[a-zA-Z]+' | tr -d ' -')
  if echo "$FLAGS" | grep -qi 'r' && echo "$FLAGS" | grep -qi 'f'; then
    BLOCKED=true
    REASON="Blocked: 'rm -rf' is a destructive recursive delete. Use 'trash' or 'rm -i' for safety."
  fi
fi

# git push --force / git push -f (but NOT --force-with-lease)
if [[ "$BLOCKED" == false ]]; then
  STRIPPED=$(echo "$UPPER" | sed 's/--FORCE-WITH-LEASE//g')
  if echo "$STRIPPED" | grep -qE 'GIT\s+PUSH\s+.*--FORCE'; then
    BLOCKED=true
    REASON="Blocked: 'git push --force' rewrites remote history. Use 'git push --force-with-lease' instead."
  elif echo "$STRIPPED" | grep -qE 'GIT\s+PUSH\s+-[a-zA-Z]*[F]'; then
    BLOCKED=true
    REASON="Blocked: 'git push -f' rewrites remote history. Use 'git push --force-with-lease' instead."
  fi
fi

# DROP TABLE
if [[ "$BLOCKED" == false ]] && echo "$UPPER" | grep -qE 'DROP\s+TABLE'; then
  BLOCKED=true
  REASON="Blocked: 'DROP TABLE' will permanently destroy a database table. Confirm with project maintainer first."
fi

# TRUNCATE
if [[ "$BLOCKED" == false ]] && echo "$UPPER" | grep -qE 'TRUNCATE\s+(TABLE\s+)?[A-Z]'; then
  BLOCKED=true
  REASON="Blocked: 'TRUNCATE' removes all rows from a table instantly and irreversibly. Use DELETE with a WHERE clause instead."
fi

# DELETE FROM without WHERE
if [[ "$BLOCKED" == false ]] && echo "$UPPER" | grep -qE 'DELETE\s+FROM\s+[A-Z_]+'; then
  if ! echo "$UPPER" | grep -qiE 'WHERE\s'; then
    BLOCKED=true
    REASON="Blocked: 'DELETE FROM' without WHERE clause will delete ALL rows. Add a WHERE clause to target specific rows."
  fi
fi

# ── Act ─────────────────────────────────────────────────────────────────
if [[ "$BLOCKED" == true ]]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT=$(pwd)

  # Log
  echo "[$TIMESTAMP] $REASON | Command: $COMMAND | Project: $PROJECT" >> "$LOG_FILE"

  # Return structured decision to Claude Code
  # Exit code 2 = block, stdout contains explanation
  echo "{\"decision\": {\"type\": \"block\", \"reason\": \"$REASON\"}}"
  exit 2
fi

# Allow
exit 0
