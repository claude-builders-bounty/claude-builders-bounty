#!/usr/bin/env bash
# Pre-tool-use hook: blocks destructive bash commands per claude-builders-bounty #3
# Install: cp block-destructive.sh ~/.claude/hooks/pre-tool-use/ && chmod +x ~/.claude/hooks/pre-tool-use/block-destructive.sh

set -uo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Read command from stdin (Claude Code passes JSON with .tool_input.command)
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ -z "$CMD" ]; then
  exit 0
fi

BLOCKED=false
REASON=""

# Check destructive patterns
if echo "$CMD" | grep -qiE '\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b'; then
  BLOCKED=true
  REASON="rm -rf detected: recursive force delete is blocked to prevent accidental data loss"
elif echo "$CMD" | grep -qiE '\bDROP\s+TABLE\b'; then
  BLOCKED=true
  REASON="DROP TABLE detected: destructive DDL without migration safety"
elif echo "$CMD" | grep -qiE '\bgit\s+push\s+.*--force\b'; then
  BLOCKED=true
  REASON="git push --force detected: can overwrite remote history irreversibly"
elif echo "$CMD" | grep -qiE '\bTRUNCATE\b'; then
  BLOCKED=true
  REASON="TRUNCATE detected: bulk data deletion without WHERE clause"
elif echo "$CMD" | grep -qiE '\bDELETE\s+FROM\b' && ! echo "$CMD" | grep -qiE '\bWHERE\b'; then
  BLOCKED=true
  REASON="DELETE FROM without WHERE clause: would delete all rows"
fi

if [ "$BLOCKED" = true ]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT_PATH=$(pwd)
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${CMD}" >> "$LOG_FILE"
  
  # Output block message to stderr for Claude to see
  echo "⛔ BLOCKED: ${REASON}" >&2
  echo "Command logged to ${LOG_FILE}" >&2
  
  # Exit with non-zero to signal block to Claude Code
  exit 1
fi

exit 0
