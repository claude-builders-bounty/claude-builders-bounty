#!/bin/bash

# Claude Code pre-tool-use hook to block destructive bash commands
# Patterns to block:
# - rm -rf
# - DROP TABLE
# - git push --force
# - TRUNCATE
# - DELETE FROM (without WHERE clause)

# Log file location
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log blocked commands
log_block() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local command="$1"
    local project_path="${PROJECT_PATH:-$(pwd)}"
    echo "[$timestamp] BLOCKED: $command (Project: $project_path)" >> "$LOG_FILE"
}

# Get the command being executed
command="$1"

# Check for destructive patterns
case "$command" in
    *"rm -rf"*)
        echo "BLOCKED: 'rm -rf' is not allowed for safety reasons"
        log_block "$command"
        exit 1
        ;;
    *"DROP TABLE"*)
        echo "BLOCKED: 'DROP TABLE' is not allowed for safety reasons"
        log_block "$command"
        exit 1
        ;;
    *"git push --force"*)
        echo "BLOCKED: 'git push --force' is not allowed for safety reasons"
        log_block "$command"
        exit 1
        ;;
    *"TRUNCATE"*)
        echo "BLOCKED: 'TRUNCATE' is not allowed for safety reasons"
        log_block "$command"
        exit 1
        ;;
    *"DELETE FROM"*"WHERE"*": "*)
        # This is a safe DELETE with WHERE clause
        ;;
    *"DELETE FROM"*)
        echo "BLOCKED: 'DELETE FROM' without WHERE clause is not allowed for safety reasons"
        log_block "$command"
        exit 1
        ;;
esac

# If we get here, the command is allowed
exit 0