#!/bin/bash

# Pre-tool-use hook to block destructive bash commands
# Place in ~/.claude/hooks/pre-tool-use-block-destructive-commands.sh

set -euo pipefail

# Log file location
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log blocked commands
log_blocked() {
    local timestamp=$(date -Iseconds)
    local project_path=$(pwd)
    echo "[$timestamp] Blocked command: $1 (Project: $project_path)" >> "$LOG_FILE"
}

# Check if this is a bash command execution
if [ "${1:-}" != "bash" ] && [ "${1:-}" != "sh" ] && [ "${1:-}" != "/bin/bash" ] && [ "${1:-}" != "/bin/sh" ]; then
    # Not a bash command, exit early
    exit 0
fi

# Shift to get the actual command
shift

# Join remaining arguments into a single command string
command_string=""
for arg in "$@"; do
    # Escape spaces in arguments
    if [[ "$arg" == *" "* ]]; then
        command_string+=" \"$arg\""
    else
        command_string+=" $arg"
    fi
done
command_string="${command_string# }"  # Remove leading space

# Check for destructive patterns
blocked=false

if [[ "$command_string" == *"rm -rf"* ]]; then
    blocked=true
    reason="rm -rf command blocked for safety"
elif [[ "$command_string" == *"DROP TABLE"* ]]; then
    blocked=true
    reason="DROP TABLE command blocked for safety"
elif [[ "$command_string" == *"git push --force"* ]]; then
    blocked=true
    reason="git push --force command blocked for safety"
elif [[ "$command_string" == *"TRUNCATE "* ]]; then
    blocked=true
    reason="TRUNCATE command blocked for safety"
elif [[ "$command_string" == *"DELETE FROM "* ]] && [[ "$command_string" != *" WHERE "* ]]; then
    blocked=true
    reason="DELETE FROM without WHERE clause blocked for safety"
fi

# If blocked, log and exit with error
if [ "$blocked" = true ]; then
    log_blocked "$command_string"
    echo "BLOCKED: $reason"
    echo "This command was blocked by the pre-tool-use safety hook."
    echo "See ~/.claude/hooks/blocked.log for details."
    exit 1
fi

exit 0