#!/bin/bash

# Configuration
HOOKS_DIR="$HOME/.claude/hooks"
LOG_FILE="$HOOKS_DIR/blocked.log"

# Create log file if it doesn't exist
touch "$LOG_FILE" 2>/dev/null

# Function to log blocked commands
log_blocked() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local project_path=$(pwd)
    echo "[$timestamp] [BLOCKED] $1 in project: $project_path" >> "$LOG_FILE"
}

# Get the command from Claude Code environment variable
command="$claude_tool_input"

# Check for destructive commands we want to block
case "$command" in
    *"rm -rf"*)
        echo "BLOCKED: 'rm -rf' command is not allowed for safety reasons" >&2
        log_blocked "rm -rf command"
        exit 1
        ;;
    *"DROP TABLE"*)
        echo "BLOCKED: 'DROP TABLE' command is not allowed for safety reasons" >&2
        log_blocked "DROP TABLE command"
        exit 1
        ;;
    *"git push --force"*)
        echo "BLOCKED: 'git push --force' command is not allowed for safety reasons" >&2
        log_blocked "git push --force command"
        exit 1
        ;;
    *"TRUNCATE"*)
        echo "BLOCKED: 'TRUNCATE' command is not allowed for safety reasons" >&2
        log_blocked "TRUNCATE command"
        exit 1
        ;;
    *"DELETE FROM "*)
        # Check if it's a DELETE FROM without a WHERE clause
        # This is a simple check - in a real implementation, you'd want more robust parsing
        if [[ "$command" =~ DELETE[[:space:]]+FROM[[:space:]]+[^[:space:]]+[[:space:]]*$ ]]; then
            echo "BLOCKED: DELETE command without WHERE clause is not allowed for safety reasons" >&2
            log_blocked "DELETE without WHERE clause"
            exit 1
        fi
        ;;
esac

# If we get here, the command is allowed
echo "ALLOWED: $command" >&2
exit 0