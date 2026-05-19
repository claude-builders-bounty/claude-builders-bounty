#!/usr/bin/env bash
# Claude Code pre-tool-use hook — blocks destructive bash commands
# Installation: copy to ~/.claude/hooks/block-destructive.sh
set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read the JSON hook input from stdin
INPUT=$(cat)

# Extract the command — Claude Code sends tool call as JSON
# The bash tool has "command" field in the input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // .command // ""')

if [[ -z "$COMMAND" ]]; then
  # Not a bash command — allow
  echo '{"continue": true}'
  exit 0
fi

# Get project path for logging
PROJECT_PATH=$(echo "$INPUT" | jq -r '.cwd // .project_path // "unknown"')

# ─── Dangerous pattern detection ───────────────────────

BLOCKED=false
REASON=""

# Normalize command: collapse whitespace, trim
NORM_CMD=$(echo "$COMMAND" | sed 's/  */ /g' | xargs)

# rm -rf (any variation)
if echo "$NORM_CMD" | grep -qE '(^|[;&| ])rm\b.*\s-rf?\b|(^|[;&| ])rm\b.*--recursive'; then
  BLOCKED=true
  REASON="rm -rf is destructive and irreversible. Use trash or move to /tmp instead."
fi

# DROP TABLE / TRUNCATE
if echo "$NORM_CMD" | grep -qiE '\bDROP\s+TABLE\b|\bTRUNCATE\s+(TABLE\s+)?\b'; then
  BLOCKED=true
  REASON="DROP TABLE / TRUNCATE destroys data permanently. Add a backup step first."
fi

# DELETE FROM without WHERE
if echo "$NORM_CMD" | grep -qiE '\bDELETE\s+FROM\b'; then
  if ! echo "$NORM_CMD" | grep -qiE '\bWHERE\b'; then
    BLOCKED=true
    REASON="DELETE FROM without WHERE clause would delete ALL rows. Add a WHERE condition."
  fi
fi

# git push --force (block only bare --force, allow --force-with-lease)
if echo "$NORM_CMD" | grep -qE '\bgit\s+push\b.*--force($|[^\-])'; then
  BLOCKED=true
  REASON="git push --force can overwrite remote history. Use --force-with-lease instead."
fi

# ─── Action ────────────────────────────────────────────

if $BLOCKED; then
  # Log the blocked attempt
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  cat >> "$LOG_FILE" <<EOF
[$TIMESTAMP] BLOCKED
  Command:  $COMMAND
  Project:  $PROJECT_PATH
  Reason:   $REASON
---
EOF

  # Return block response to Claude Code
  jq -n --arg reason "$REASON" '{
    continue: false,
    reason: $reason
  }'
  exit 0
fi

# Safe command — allow
echo '{"continue": true}'
