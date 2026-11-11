#!/usr/bin/env bash
# POSIX shell implementation for pre-tool-use command interception
set -euo pipefail

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
mkdir -p "${LOG_DIR}"

CMD="$*"
if [ -z "${CMD}" ]; then
  if [ ! -t 0 ]; then
    CMD=$(cat)
  fi
fi

if [ -z "${CMD}" ]; then
  exit 0
fi

REASON=""

if echo "${CMD}" | grep -Eiq '\brm\s+.*(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)'; then
  REASON="Recursive force removal (rm -rf / rm -fr) is prohibited."
elif echo "${CMD}" | grep -Eiq '\bDROP\s+TABLE\b'; then
  REASON="Dropping database tables (DROP TABLE) is prohibited."
elif echo "${CMD}" | grep -Eiq '\bgit\s+push\b.*(\s+--force|\s+-f)\b'; then
  REASON="Force-pushing git branches (git push --force) is prohibited."
elif echo "${CMD}" | grep -Eiq '\bTRUNCATE(\s+TABLE)?\b'; then
  REASON="Table truncation (TRUNCATE) is prohibited."
elif echo "${CMD}" | grep -Eiq '\bDELETE\s+FROM\b' && ! echo "${CMD}" | grep -Eiq '\bWHERE\b'; then
  REASON="Deleting records without an explicit WHERE clause is prohibited."
fi

if [ -n "${REASON}" ]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT_PATH=$(pwd)
  echo "[${TIMESTAMP}] PROJECT=${PROJECT_PATH} REASON=${REASON} COMMAND=${CMD}" >> "${LOG_FILE}"
  echo "" >&2
  echo "🛑 [BLOCKED BY CLAUDE CODE HOOK]: ${REASON}" >&2
  echo "Attempted Command: ${CMD}" >&2
  echo "Logged to: ${LOG_FILE}" >&2
  echo "" >&2
  exit 1
fi

exit 0
