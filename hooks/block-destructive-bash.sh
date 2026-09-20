#!/usr/bin/env bash
# ==============================================================================
# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
# Complies with Opire Bounty #3 Acceptance Criteria
# ==============================================================================

set -uo pipefail

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
mkdir -p "${LOG_DIR}" 2>/dev/null || true

# Extract command string from input (JSON payload or raw argument)
CMD_INPUT="${1:-}"
if [ -z "${CMD_INPUT}" ] && [ ! -t 0 ]; then
    # Read from stdin
    RAW_STDIN=$(cat)
    # Check if JSON format with "command" field
    if echo "${RAW_STDIN}" | grep -q '"command"'; then
        CMD_INPUT=$(echo "${RAW_STDIN}" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    else
        CMD_INPUT="${RAW_STDIN}"
    fi
fi

if [ -z "${CMD_INPUT}" ]; then
    exit 0
fi

# Function to log blocked attempt
log_blocked() {
    local reason="$1"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")
    echo "[${timestamp}] BLOCKED: "${CMD_INPUT}" | REASON: ${reason}" >> "${LOG_FILE}"
    echo "::error::[PRE-TOOL-USE HOOK BLOCKED] Destructive command rejected: ${reason}" >&2
    echo "Command: ${CMD_INPUT}" >&2
    exit 2
}

# 1. Block rm -rf variants (rm -rf, rm -fr, rm -r -f, rm --recursive --force)
if echo "${CMD_INPUT}" | grep -E -q 'rm\s+.*(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive)'; then
    log_blocked "Dangerous recursive file deletion (rm -rf)"
fi

# 2. Block git push --force / -f
if echo "${CMD_INPUT}" | grep -E -q 'git\s+push\s+.*(\-\-force|\-f|\+refs/)'; then
    log_blocked "Force pushing to git remote (git push --force)"
fi

# 3. Block SQL DROP TABLE / DATABASE / SCHEMA / VIEW
if echo "${CMD_INPUT}" | grep -E -i -q 'DROP\s+(TABLE|DATABASE|SCHEMA|VIEW)'; then
    log_blocked "Destructive database drop statement (DROP TABLE/DATABASE)"
fi

# 4. Block SQL TRUNCATE TABLE
if echo "${CMD_INPUT}" | grep -E -i -q 'TRUNCATE(\s+TABLE)?\s+\w+'; then
    log_blocked "Table truncation statement (TRUNCATE)"
fi

# 5. Block SQL DELETE FROM without WHERE clause
if echo "${CMD_INPUT}" | grep -E -i -q 'DELETE\s+FROM\s+\w+' && ! echo "${CMD_INPUT}" | grep -E -i -q 'WHERE'; then
    log_blocked "Unbounded DELETE statement missing WHERE clause"
fi

# 6. Block raw disk formatting / wiping
if echo "${CMD_INPUT}" | grep -E -q 'dd\s+.*of=/dev/(sd[a-z]|nvme[0-9]|hd[a-z]|disk[0-9])'; then
    log_blocked "Direct disk device write (dd of=/dev/...)"
fi
if echo "${CMD_INPUT}" | grep -E -q 'mkfs(\.[a-z0-9]+)?\s+'; then
    log_blocked "Filesystem formatting command (mkfs)"
fi

# Command is safe
exit 0
