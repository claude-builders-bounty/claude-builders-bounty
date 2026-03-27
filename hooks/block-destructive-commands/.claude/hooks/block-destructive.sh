#!/usr/bin/env bash
# PreToolUse hook for Claude Code — blocks destructive bash commands.
# See: https://code.claude.com/docs/en/hooks

set -euo pipefail

# Ensure jq is available
if ! command -v jq &>/dev/null; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"jq is required but not installed"}}' 
  exit 0
fi

# Read tool input from stdin
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Nothing to check if command is empty
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Log path
LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"

# Patterns to block (case-insensitive grep -iE)
BLOCKED_PATTERNS=(
  'rm\s+-[a-zA-Z]*r[a-zA-Z]*f'      # rm -rf (any flag combo with r and f)
  'rm\s+--recursive\s+--force'        # rm --recursive --force
  'DROP\s+TABLE'                      # SQL DROP TABLE
  'git\s+push\s+--force'              # force push
  'git\s+push\s+-f\b'                 # force push shorthand
  'TRUNCATE'                          # SQL TRUNCATE
)

BLOCKED_REASONS=(
  "Recursive force delete (rm -rf) blocked"
  "Recursive force delete (rm --recursive --force) blocked"
  "SQL DROP TABLE blocked"
  "Git force push (git push --force) blocked"
  "Git force push (git push -f) blocked"
  "SQL TRUNCATE blocked"
)

# Special check: DELETE FROM without WHERE (case-insensitive)
if echo "$COMMAND" | grep -qiE 'DELETE\s+FROM' && ! echo "$COMMAND" | grep -qiE 'DELETE\s+FROM.*WHERE'; then
  mkdir -p "$LOG_DIR"
  REASON="SQL DELETE FROM without WHERE clause blocked. Command: ${COMMAND}"
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] BLOCKED | ${REASON} | PWD: ${PWD}" >> "$LOG_FILE"
  jq -n --arg reason "$REASON" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
  exit 0
fi

for i in "${!BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "${BLOCKED_PATTERNS[$i]}"; then
    # Log the blocked attempt
    mkdir -p "$LOG_DIR"
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] BLOCKED | ${BLOCKED_REASONS[$i]} | Command: ${COMMAND} | PWD: ${PWD}" >> "$LOG_FILE"

    # Deny the command
    jq -n --arg reason "${BLOCKED_REASONS[$i]}. Command: ${COMMAND}" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $reason
      }
    }'
    exit 0
  fi
done

# Command is safe — allow it
exit 0
