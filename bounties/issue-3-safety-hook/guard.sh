#!/usr/bin/env bash
# guard.sh — Pre-tool-use hook that blocks destructive bash commands
# Input: JSON on stdin with tool_input.command field
# Output: exit 2 to block, exit 0 to allow

set -euo pipefail

# Read command from stdin JSON
COMMAND=$(jq -r '.tool_input.command // empty' 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Log directory
LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
mkdir -p "$LOG_DIR"

# Timestamp for logging
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
PROJECT_PATH=$(jq -r '.cwd // "unknown"' 2>/dev/null)

# ── Patterns to block ────────────────────────────────────────────────────────

# Destructive file operations
if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+/' ; then
  echo "[BLOCKED] rm -rf / detected — recursive root deletion" >&2
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"Blocked rm -rf / — recursive root deletion is extremely dangerous. If intentional, use the hook bypass.\"}}" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+' ; then
  echo "[BLOCKED] rm -rf detected — confirm this is intentional" >&2
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"rm -rf detected. Confirm directory deletion is intentional.\"}}" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

# Destructive SQL
if echo "$COMMAND" | grep -qiE '\bDROP\s+TABLE\b' ; then
  echo "[BLOCKED] DROP TABLE detected — irreversible table deletion" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qiE '\bTRUNCATE\b' ; then
  echo "[BLOCKED] TRUNCATE detected — irreversible data wipe" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qiE '\bDELETE\s+FROM\b' && ! echo "$COMMAND" | grep -qiE '\bWHERE\b' ; then
  echo "[BLOCKED] DELETE FROM without WHERE — would delete all rows" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

# Destructive git operations
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force' ; then
  echo "[BLOCKED] git push --force detected — rewrites remote history" >&2
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"git push --force rewrites remote history. Ensure this is safe for collaborators.\"}}" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard' ; then
  echo "[BLOCKED] git reset --hard detected — discards all uncommitted changes" >&2
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"git reset --hard discards all uncommitted changes permanently.\"}}" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qE 'git\s+clean\s+-f' ; then
  echo "[BLOCKED] git clean -f detected — deletes untracked files" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qE 'git\s+branch\s+-D\b' ; then
  echo "[BLOCKED] git branch -D detected — force deletes a branch" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

# Destructive system operations
if echo "$COMMAND" | grep -qE 'chmod\s+-R\s+777' ; then
  echo "[BLOCKED] chmod -R 777 detected — makes all files world-writable" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qE '> /dev/sd[a-z]' ; then
  echo "[BLOCKED] Write to block device detected — would destroy disk data" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qE 'mkfs\.' ; then
  echo "[BLOCKED] mkfs detected — would format a filesystem" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

if echo "$COMMAND" | grep -qE 'dd\s+.*of=/dev/' ; then
  echo "[BLOCKED] dd to device detected — would overwrite disk data" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

# Destructive package operations
if echo "$COMMAND" | grep -qE 'npm\s+publish\s+--force' ; then
  echo "[BLOCKED] npm publish --force detected — would overwrite published package" >&2
  echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
  exit 2
fi

# Pass through — command is safe
exit 0
