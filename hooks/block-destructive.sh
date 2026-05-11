#!/usr/bin/env bash
# block-destructive.sh — Claude Code PreToolUse hook
# Intercepts and blocks destructive bash commands before execution.
#
# Install:
#   cp hooks/block-destructive.sh ~/.claude/hooks/
#   Add to ~/.claude/settings.json (see README)

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read the tool input from stdin (Claude Code pipes JSON)
INPUT=$(cat)

# Extract the tool name and command
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

# Only inspect Bash tool calls
if [[ "$TOOL_NAME" != "Bash" ]]; then
  echo "$INPUT"
  exit 0
fi

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [[ -z "$COMMAND" ]]; then
  echo "$INPUT"
  exit 0
fi

# Project path from environment or pwd
PROJECT_PATH="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

# --- Destructive pattern definitions ---
# Each pattern has a regex and a human-readable reason.
declare -a PATTERNS
declare -a REASONS

# rm -rf (recursive force delete)
PATTERNS+=('rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|(-[a-zA-Z]*f[a-zA-Z]*r))\s')
REASONS+=('rm -rf: recursive force deletion can destroy entire directory trees')

# rm -rf with flags in any order (e.g., rm --force -r)
PATTERNS+=('rm\s+--force\s+(-r|--recursive)')
REASONS+=('rm --force --recursive: recursive force deletion')

# DROP TABLE
PATTERNS+=('DROP\s+TABLE')
REASONS+=('DROP TABLE: permanently destroys database tables and all data')

# DROP DATABASE
PATTERNS+=('DROP\s+DATABASE')
REASONS+=('DROP DATABASE: permanently destroys entire databases')

# TRUNCATE TABLE
PATTERNS+=('TRUNCATE(\s+TABLE)?')
REASONS+=('TRUNCATE: removes all rows from a table without logging individual deletions')

# DELETE FROM without WHERE clause
PATTERNS+=('DELETE\s+FROM\s+\S+\s*;')
REASONS+=('DELETE FROM without WHERE: deletes all rows from a table')

# DELETE FROM at end of command (no WHERE, no semicolon)
PATTERNS+=('DELETE\s+FROM\s+\S+\s*$')
REASONS+=('DELETE FROM without WHERE: deletes all rows from a table')

# git push --force (including -f shorthand)
PATTERNS+=('git\s+push\s+(-[a-zA-Z]*f|--force)')
REASONS+=('git push --force: overwrites remote history, can destroy team members'\'' work')

# git reset --hard
PATTERNS+=('git\s+reset\s+--hard')
REASONS+=('git reset --hard: discards all uncommitted changes permanently')

# git clean -f (force remove untracked files)
PATTERNS+=('git\s+clean\s+-[a-zA-Z]*f')
REASONS+=('git clean -f: permanently removes untracked files')

# chmod 777 (overly permissive)
PATTERNS+=('chmod\s+777')
REASONS+=('chmod 777: sets world-readable/writable/executable — a security risk')

# mkfs (format filesystem)
PATTERNS+=('mkfs\.')
REASONS+=('mkfs: formats a filesystem, destroying all data on the device')

# dd with of= (raw disk write)
PATTERNS+=('dd\s+.*of=/dev/')
REASONS+=('dd to device: raw disk write can destroy partitions and data')

# --- Check each pattern ---
blocked=false
block_reason=""

for i in "${!PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "${PATTERNS[$i]}"; then
    blocked=true
    block_reason="${REASONS[$i]}"
    break
  fi
done

if [[ "$blocked" == "true" ]]; then
  # Log the blocked attempt
  echo "${TIMESTAMP} | BLOCKED | ${block_reason} | command: ${COMMAND} | project: ${PROJECT_PATH}" >> "$LOG_FILE"

  # Output error message for Claude to see
  cat >&2 <<EOF
[BLOCKED] Destructive command intercepted by block-destructive hook.

Reason: ${block_reason}
Command: ${COMMAND}

This command was blocked because it could cause irreversible damage.
If this action is truly needed, ask the user to run it manually outside Claude Code.

Logged to: ${LOG_FILE}
EOF
  exit 2
fi

# Command is safe — pass through
echo "$INPUT"
exit 0
