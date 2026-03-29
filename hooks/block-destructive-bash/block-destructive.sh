#!/bin/bash
# block-destructive.sh — Claude Code PreToolUse hook
# Blocks dangerous bash commands before execution and logs attempts.
#
# Blocked patterns:
#   - rm -rf (recursive force delete)
#   - DROP TABLE (SQL table destruction)
#   - git push --force / -f (force push)
#   - TRUNCATE (SQL table truncation)
#   - DELETE FROM without WHERE clause
#
# Usage: Configured as a PreToolUse hook in Claude Code settings.
# Input: JSON on stdin with tool_name and tool_input.command
# Output: JSON with permissionDecision "deny" if blocked, or exit 0 to allow.

set -euo pipefail

# --- Configuration ---
LOG_FILE="${HOME}/.claude/hooks/blocked.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# --- Read input ---
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
PROJECT_DIR=$(echo "$INPUT" | jq -r '.session.project_directory // .cwd // "unknown"')

# If no command found, allow (not a bash tool call we care about)
if [ -z "$COMMAND" ]; then
  exit 0
fi

# --- Helper: log and deny ---
deny() {
  local reason="$1"
  local timestamp
  timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

  # Log the blocked attempt
  echo "${timestamp} | BLOCKED | ${reason} | project=${PROJECT_DIR} | command=${COMMAND}" >> "$LOG_FILE"

  # Return deny decision to Claude Code
  jq -n \
    --arg reason "$reason" \
    '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $reason
      }
    }'
  exit 0
}

# --- Pattern checks ---
# Each check uses case-insensitive matching where appropriate.

# 1. rm -rf (with any flag ordering like rm -f -r, rm --recursive --force, etc.)
if echo "$COMMAND" | grep -qE '\brm\b.*-[a-zA-Z]*r[a-zA-Z]*f|\brm\b.*-[a-zA-Z]*f[a-zA-Z]*r|\brm\b.*--recursive.*--force|\brm\b.*--force.*--recursive|\brm\b.*-r\b.*-f\b|\brm\b.*-f\b.*-r\b'; then
  deny "BLOCKED: 'rm -rf' detected. Recursive force deletion is not allowed."
fi

# 2. DROP TABLE (SQL — case insensitive)
if echo "$COMMAND" | grep -qiE '\bDROP\s+TABLE\b'; then
  deny "BLOCKED: 'DROP TABLE' detected. Dropping database tables is not allowed."
fi

# 3. git push --force or git push -f
if echo "$COMMAND" | grep -qE '\bgit\s+push\b.*(\s--force\b|\s-f\b)'; then
  deny "BLOCKED: 'git push --force' detected. Force pushing is not allowed."
fi

# 4. TRUNCATE (SQL — case insensitive)
if echo "$COMMAND" | grep -qiE '\bTRUNCATE\b'; then
  deny "BLOCKED: 'TRUNCATE' detected. Truncating tables is not allowed."
fi

# 5. DELETE FROM without WHERE (SQL — case insensitive)
# Match DELETE FROM ... but ensure no WHERE clause follows
if echo "$COMMAND" | grep -qiE '\bDELETE\s+FROM\b'; then
  if ! echo "$COMMAND" | grep -qiE '\bDELETE\s+FROM\b.*\bWHERE\b'; then
    deny "BLOCKED: 'DELETE FROM' without WHERE clause detected. Unfiltered deletes are not allowed."
  fi
fi

# --- All checks passed — allow the command ---
exit 0
