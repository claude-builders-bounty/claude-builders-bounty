#!/bin/bash

# Block destructive bash commands hook for Claude Code

HOOKS_DIR="$HOME/.claude/hooks"
LOG_FILE="$HOOKS_DIR/blocked.log"

# Create log file if it doesn't exist
touch "$LOG_FILE"

# Function to log blocked commands
log_blocked() {
    echo "$(date): $1 [Project: $2]" >> "$LOG_FILE"
}

# Read from stdin (the command being executed)
read COMMAND

# Check for destructive patterns
if [[ "$COMMAND" =~ ^.*"rm -rf".*$ ]] || \
   [[ "$COMMAND" =~ ^.*"DROP TABLE".*$ ]] || \
   [[ "$COMMAND" =~ ^.*"git push --force".*$ ]] || \
   [[ "$COMMAND" =~ ^.*"TRUNCATE".*$ ]] || \
   [[ "$COMMAND" =~ DELETE\ FROM\ .*[^(WHERE).*] ]] || \
   [[ "$COMMAND" =~ DELETE\ FROM\ [^ ]*$', Project: '.*$ ]]; then
    log_blocked "$COMMAND" "$PROJECT_PATH"
    echo "ERROR: Blocked destructive command: $COMMAND"
    echo "This command was blocked for security reasons."
    echo "Check $LOG_FILE for details."
    exit 1
fi

# If we get here, the command is safe to execute
echo "$COMMAND"

exit 0