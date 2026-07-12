#!/bin/bash

# Pre-tool-use hook that blocks destructive bash commands
# Save as: ~/.claude/hooks/block-destructive-commands.sh

# Log file location
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Get the command being executed
COMMAND="$1"

# Get project path (current working directory)
PROJECT_PATH="$(pwd)"

# Get timestamp
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Function to log blocked commands
log_blocked_command() {
    echo "[$TIMESTAMP] $COMMAND in $PROJECT_PATH" >> "$LOG_FILE"
}

# Check for destructive patterns
if [[ "$COMMAND" == *"rm -rf"* ]]; then
    log_blocked_command
    echo "🚫 Destructive command blocked: 'rm -rf' is not allowed"
    exit 1
elif [[ "$COMMAND" == *"DROP TABLE"* ]]; then
    log_blocked_command
    echo "🚫 Destructive command blocked: 'DROP TABLE' is not allowed"
    exit 1
elif [[ "$COMMAND" == *"git push --force"* ]]; then
    log_blocked_command
    echo "🚫 Destructive command blocked: 'git push --force' is not allowed"
    exit 1
elif [[ "$COMMAND" == *"TRUNCATE"* ]]; then
    log_blocked_command
    echo "🚫 Destructive command blocked: 'TRUNCATE' is not allowed"
    exit 1
elif [[ "$COMMAND" == *"DELETE FROM"* ]] && [[ "$COMMAND" != *"WHERE"* ]]; then
    log_blocked_command
    echo "🚫 Destructive command blocked: 'DELETE FROM' without WHERE clause is not allowed"
    exit 1
fi

# If we get here, the command is allowed
exit 0