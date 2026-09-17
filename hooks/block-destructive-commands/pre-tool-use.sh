#!/usr/bin/env bash
# ==============================================================================
# Claude Code pre-tool-use Hook: Destructive Bash Command Blocker
# Intercepts and blocks dangerous commands before execution in Claude Code.
# Complies with Claude Code Hook API Specification (~/.claude/hooks/)
# ==============================================================================

set -euo pipefail

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
mkdir -p "${LOG_DIR}"

# 1. Read payload from arguments or standard input
INPUT_DATA=""
if [ $# -gt 0 ]; then
  INPUT_DATA="$*"
else
  # Read stdin if available (non-blocking check)
  if [ ! -t 0 ]; then
    INPUT_DATA=$(cat -)
  fi
fi

if [ -z "${INPUT_DATA}" ]; then
  # No command data passed, allow execution
  exit 0
fi

# 2. Extract command string if payload is JSON
COMMAND="${INPUT_DATA}"
if echo "${INPUT_DATA}" | grep -q '^{' 2>/dev/null; then
  # Extract tool_name and command from JSON payload if present
  EXTRACTED_CMD=$(echo "${INPUT_DATA}" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed -E 's/"command"[[:space:]]*:[[:space:]]*"([^"]*)"/\1/' || true)
  if [ -n "${EXTRACTED_CMD}" ]; then
    COMMAND="${EXTRACTED_CMD}"
  fi
fi

# 3. Security Inspection Rules
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BLOCKED=0
REASON=""
TRIGGER=""

# Rule A: rm -rf (recursive force deletion)
if echo "${COMMAND}" | grep -Eq 'rm[[:space:]]+(-[a-zA-Z0-9]*r[a-zA-Z0-9]*f|-[a-zA-Z0-9]*f[a-zA-Z0-9]*r|--recursive[[:space:]]+--force|--force[[:space:]]+--recursive)'; then
  BLOCKED=1
  TRIGGER="rm -rf"
  REASON="Dangerous recursive force deletion detected"

# Rule B: DROP TABLE / DATABASE / SCHEMA
elif echo "${COMMAND}" | grep -Eiq 'DROP[[:space:]]+(TABLE|DATABASE|SCHEMA|VIEW)[[:space:]]+'; then
  BLOCKED=1
  TRIGGER="DROP TABLE"
  REASON="Database destruction statement detected"

# Rule C: git push --force / -f
elif echo "${COMMAND}" | grep -Eq 'git[[:space:]]+push[[:space:]]+.*(--force|-f([[:space:]]|$)|--force-with-lease[[:space:]]*=[[:space:]]*false|\+refs/)'; then
  BLOCKED=1
  TRIGGER="git push --force"
  REASON="Destructive remote git branch overwrite detected"

# Rule D: TRUNCATE
elif echo "${COMMAND}" | grep -Eiq 'TRUNCATE([[:space:]]+TABLE)?[[:space:]]+'; then
  BLOCKED=1
  TRIGGER="TRUNCATE"
  REASON="Table truncation / bulk data purge statement detected"

# Rule E: DELETE FROM without WHERE clause
elif echo "${COMMAND}" | grep -Eiq 'DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z0-9_`".]+' && ! echo "${COMMAND}" | grep -Eiq 'WHERE[[:space:]]+'; then
  BLOCKED=1
  TRIGGER="DELETE FROM without WHERE"
  REASON="Unbounded DELETE statement without WHERE clause detected"
fi

# 4. Handle Block or Allow
if [ "${BLOCKED}" -eq 1 ]; then
  # Format log line: [TIMESTAMP] [TRIGGER] Reason | Command
  LOG_ENTRY="[${TIMESTAMP}] [BLOCKED:${TRIGGER}] Reason: ${REASON} | Command: \"${COMMAND}\""
  echo "${LOG_ENTRY}" >> "${LOG_FILE}"

  # User-facing security rejection message
  >&2 echo "================================================================================"
  >&2 echo "🚨 [SECURITY HOOK BLOCKED] Command rejected by Claude Code pre-tool-use guard"
  >&2 echo "--------------------------------------------------------------------------------"
  >&2 echo "Trigger: ${TRIGGER}"
  >&2 echo "Reason:  ${REASON}"
  >&2 echo "Command: ${COMMAND}"
  >&2 echo "Logged to: ${LOG_FILE}"
  >&2 echo "================================================================================"

  # Exit non-zero to instruct Claude Code to cancel tool execution
  exit 1
fi

# Command passed security inspection
exit 0
