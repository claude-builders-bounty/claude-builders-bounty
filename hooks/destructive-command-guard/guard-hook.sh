#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  Claude Code Pre-Tool-Use Hook: Destructive Command Guard
#  Blocks dangerous bash commands before execution.
#
#  Hooks spec: reads JSON from stdin with tool_name and tool_input,
#  exits 0 to allow, exits 2 to block (with reason on stdout).
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="${PWD}"

# Read the hook payload from stdin
PAYLOAD=$(cat)

# Extract tool name and input
TOOL_NAME=$(echo "$PAYLOAD" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_name', ''))
" 2>/dev/null || echo "")

# Only inspect bash/shell tool calls
if [[ "$TOOL_NAME" != "bash" && "$TOOL_NAME" != "terminal" && "$TOOL_NAME" != "shell" ]]; then
    exit 0
fi

# Extract the command being run
COMMAND=$(echo "$PAYLOAD" | python3 -c "
import sys, json
data = json.load(sys.stdin)
inp = data.get('tool_input', {})
# Handle different input formats
cmd = inp.get('command', '') or inp.get('cmd', '') or inp.get('content', '')
print(cmd)
" 2>/dev/null || echo "")

# If we can't parse the command, allow it (fail open)
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# ─────────────────────────────────────────────────────────────────
#  PATTERN DEFINITIONS
#  Each pattern has: regex, description, severity
# ─────────────────────────────────────────────────────────────────

declare -A PATTERNS
declare -A DESCRIPTIONS

# Filesystem destruction
PATTERNS[rm_rf]='rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+(-[a-zA-Z]*r[a-zA-Z]*|[/~])|(-[a-zA-Z]*r[a-zA-Z]*\s+(-[a-zA-Z]*f[a-zA-Z]*|[/~]))|--no-preserve-root)'
DESCRIPTIONS[rm_rf]="Recursive forced deletion detected (rm -rf). This can destroy your filesystem."

PATTERNS[rm_root]='rm\s+.*\s+/\s*$|rm\s+.*\s+/[^a-zA-Z]'
DESCRIPTIONS[rm_root]="Deletion targeting root filesystem (/) detected."

# Database destruction
PATTERNS[drop_table]='DROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\s'
DESCRIPTIONS[drop_table]="SQL DROP statement detected. This permanently deletes database objects."

PATTERNS[truncate]='TRUNCATE\s+(TABLE\s+)?\w'
DESCRIPTIONS[truncate]="SQL TRUNCATE detected. This removes all rows from a table irreversibly."

PATTERNS[delete_no_where]='DELETE\s+FROM\s+\w+\s*;|DELETE\s+FROM\s+\w+\s*$'
DESCRIPTIONS[delete_no_where]="DELETE FROM without WHERE clause detected. This deletes ALL rows in the table."

# Git destruction
PATTERNS[force_push]='git\s+push\s+.*(-f|--force)\b'
DESCRIPTIONS[force_push]="git push --force detected. This rewrites remote history and can cause data loss."

PATTERNS[force_push2]='git\s+push\s+--force'
DESCRIPTIONS[force_push2]="git push --force detected. This rewrites remote history and can cause data loss."

# Additional dangerous patterns
PATTERNS[dd_disk]='dd\s+.*of=/dev/'
DESCRIPTIONS[dd_disk]="dd writing to block device detected. This can overwrite disk partitions."

PATTERNS[mkfs]='mkfs\.'
DESCRIPTIONS[mkfs]="Filesystem format command (mkfs) detected. This destroys all data on the partition."

PATTERNS[chmod_777]='chmod\s+(-R\s+)?777\s+/'
DESCRIPTIONS[chmod_777]="Recursive chmod 777 on root path detected. This is a severe security risk."

PATTERNS[curl_pipe_sh]='curl\s+.*\|\s*(sudo\s+)?(ba)?sh'
DESCRIPTIONS[curl_pipe_sh]="Piping curl output to shell detected. This executes unverified remote code."

PATTERNS[wget_pipe_sh]='wget\s+.*\|\s*(sudo\s+)?(ba)?sh'
DESCRIPTIONS[wget_pipe_sh]="Piping wget output to shell detected. This executes unverified remote code."

# ─────────────────────────────────────────────────────────────────
#  CHECK COMMAND AGAINST ALL PATTERNS
# ─────────────────────────────────────────────────────────────────

for key in "${!PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -iqP "${PATTERNS[$key]}" 2>/dev/null; then
        DESCRIPTION="${DESCRIPTIONS[$key]}"
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        # Log the blocked attempt
        mkdir -p "$(dirname "$LOG_FILE")"
        echo "${TIMESTAMP} | BLOCKED [${key}] | project=${PROJECT_PATH} | command=${COMMAND}" >> "$LOG_FILE"

        # Output block reason (Claude sees this)
        cat <<EOF
{
  "decision": "block",
  "reason": "🛑 BLOCKED: ${DESCRIPTION}\n\nAttempted command: ${COMMAND}\n\nIf you believe this command is safe, please rephrase it or ask the user for explicit approval."
}
EOF
        exit 2
    fi
done

# Command is safe — allow execution
exit 0
