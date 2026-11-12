#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands (POSIX shell)
set -euo pipefail

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Read command from stdin (JSON payload or raw string) or arguments
RAW_INPUT=""
if [ ! -t 0 ]; then
  RAW_INPUT=$(cat || true)
fi

CMD=""
if [ -n "${RAW_INPUT}" ]; then
  # Try extracting command from JSON if jq or python3 is available
  if command -v python3 >/dev/null 2>&1; then
    CMD=$(python3 -c "
import sys, json
try:
    d = json.loads('''${RAW_INPUT}''')
    print(d.get('input', {}).get('command') or d.get('command') or '''${RAW_INPUT}''')
except:
    print('''${RAW_INPUT}''')
" 2>/dev/null || echo "${RAW_INPUT}")
  else
    CMD="${RAW_INPUT}"
  fi
elif [ "$#" -gt 0 ]; then
  CMD="$*"
fi

if [ -z "${CMD}" ]; then
  exit 0
fi

# Evaluation
BLOCKED=0
REASON=""

# 1. rm -rf variations
if echo "${CMD}" | grep -Eqi '\brm\s+(-[a-zA-Z0-9]*[rf][a-zA-Z0-9]*\s*)+|--recursive.*--force|--force.*--recursive'; then
  BLOCKED=1
  REASON="Recursive force file deletion (rm -rf / rm -fr) is prohibited by safety policy."
# 2. DROP TABLE
elif echo "${CMD}" | grep -Eqi '\bDROP\s+TABLE\b'; then
  BLOCKED=1
  REASON="Dropping database tables (DROP TABLE) is prohibited by safety policy."
# 3. git push --force / -f
elif echo "${CMD}" | grep -Eqi '\bgit\s+push\b.*(\s+--force\b|\s+-f\b|\s+--force-with-lease\b)'; then
  BLOCKED=1
  REASON="Force-pushing git branches (git push --force / -f) is prohibited by safety policy."
# 4. TRUNCATE TABLE
elif echo "${CMD}" | grep -Eqi '\bTRUNCATE(\s+TABLE)?\b'; then
  BLOCKED=1
  REASON="Truncating database tables (TRUNCATE) is prohibited by safety policy."
# 5. DELETE FROM without WHERE
elif echo "${CMD}" | grep -Eqi '\bDELETE\s+FROM\b' && ! echo "${CMD}" | grep -Eqi '\bWHERE\b'; then
  BLOCKED=1
  REASON="Deleting database records without a WHERE clause (DELETE FROM table) is prohibited by safety policy."
fi

if [ "${BLOCKED}" -eq 1 ]; then
  mkdir -p "${LOG_DIR}"
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "[${TIMESTAMP}] PROJECT=${PROJECT_DIR} REASON=${REASON} ATTEMPTED_COMMAND=${CMD}" >> "${LOG_FILE}"

  >&2 echo ""
  >&2 echo "============================================================"
  >&2 echo "🛑 [BLOCKED BY CLAUDE CODE PRE-TOOL-USE HOOK]"
  >&2 echo "============================================================"
  >&2 echo "Reason: ${REASON}"
  >&2 echo "Attempted Command: ${CMD}"
  >&2 echo "Project Path: ${PROJECT_DIR}"
  >&2 echo "Audit Log: ${LOG_FILE}"
  >&2 echo "============================================================"
  >&2 echo ""
  exit 1
fi

exit 0
