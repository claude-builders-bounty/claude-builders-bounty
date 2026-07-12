#!/bin/bash
#
# Hook to block destructive bash commands
#

LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Create the log file if it doesn't exist
touch "$LOG_FILE" 2>/dev/null

# Function to log blocked commands
log_blocked_command() {
    echo "$(date): Blocked command: $1 in project $2" >> "$LOG_FILE"
}

# Get the command being executed
command="$1"
project_path="$2"

# Check for destructive patterns
if [[ "$command" == "rm -rf"* || \
      "$command" == "DROP TABLE"* || \
      "$command" == *"git push --force"* || \
      "$command" == *"TRUNCATE"* || \
      "$command" == *"DELETE FROM"* ]]; then
    # Only block if there's no WHERE clause for DELETE statements
    if [[ "$command" == *"DELETE FROM"* && "$command" != *"--where"* ]]; then
        echo "Blocked: DELETE FROM without WHERE clause is not allowed"
        log_blocked_command "$command" "$PWD"
        exit 1
    fi
    
    # Block rm -rf
    if [[ "$command" == "rm -rf"* ]]; then
        echo "Blocked: Destructive command 'rm -rf' detected"
        log_blocked_command "$command" "$project_path"
        exit 1
    fi
    
    # Block DROP TABLE
    if [[ "$command" == *"DROP TABLE"* ]]; then
        echo "Blocked: DROP TABLE command is not allowed"
        log_blocked_command "$command" "$project_path"
        exit 1
    fi
    
    # Block git push --force
    if [[ "$command" == *"git push --force" ]]; then
        echo "Blocked: 'git push --force' is not allowed"
        log_blocked_command "$command" "$project_path"
        exit 1
    fi
    
    # Block TRUNCATE
    if [[ "$command" == *"TRUNCATE"* ]]; then
        echo "Blocked: TRUNCATE command is not allowed"
        log_blocked_command "$command" "$project_path"
        exit 1
    fi
fi
exit 0