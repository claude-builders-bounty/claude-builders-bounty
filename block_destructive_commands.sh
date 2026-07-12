#!/bin/bash

# Block destructive bash commands before they are executed
#
# This hook follows the Claude Code hooks format for pre-tool-use interception
#
# Installation:
# 1. Place in ~/.claude/hooks/
# 2. Ensure the hook is executable: chmod +x block_destructive_commands.sh

set -euo pipefail

# Log file location
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Get the command being executed
COMMAND="$1"

# Function to log blocked commands
log_blocked_command() {
    echo "$(date -Iseconds) - Blocked command in project $PWD: $COMMAND" >> "$LOG_FILE"
}

# Check if command matches any destructive patterns
if [[ "$COMMAND" == "rm -rf"* ]] || \
   [[ "$COMMAND" == *"DROP TABLE"* ]] || \
   [[ "$COMMAND" == *"TRUNCATE"* ]] || \
   [[ "$COMMAND" == *"DELETE FROM"*" WHERE "* ]] || \
   [[ "$COMMAND" == *"git push --force"* ]]; then
    log_blocked_command
    echo "🛑 Claude, this command has been blocked for safety:"
    echo "  $COMMAND"
    echo "Destructive commands like 'rm -rf', 'DROP TABLE', 'TRUNCATE', and 'DELETE FROM' queries without WHERE clauses are blocked."
    echo "See ~/.claude/hooks/blocked.log for details."
    exit 1
fi

# Block specific patterns
case "$COMMAND" in
    *"rm -rf"*)
        echo "$(date -Iseconds) - Blocked: $COMMAND in $PWD" >> "$LOG_FILE"
        echo "Blocked attempt to execute destructive command: $COMMAND"
        exit 1
        ;;
    *"DROP TABLE"*)
        echo "$(date -Iseconds) - Blocked: $COMMAND in $PWD" >> "$LOG_FILE"
        echo "Blocked attempt to execute destructive command: $COMMAND"
        exit 1
        ;;
    *"TRUNCATE"*|*"DELETE FROM"*" WHERE "*)
        echo "$(date -Iseconds) - Blocked: $COMMAND in $PWD" >> "$LOG_FILE"
        echo "Blocked attempt to execute destructive command: $COMMAND"
        exit 1
        ;;
    *"git push --force"*)
        echo "$(date -Iseconds) - Blocked: $COMMAND in $PWD" >> "$LOG_FILE"
        echo "Blocked attempt to execute destructive command: $COMMAND"
        exit 1
        ;;
esac

# If we are here, it means the command is not blocked
echo "Command allowed: $COMMAND"
exit 0