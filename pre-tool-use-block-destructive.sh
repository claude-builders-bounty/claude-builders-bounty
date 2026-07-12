#!/bin/bash

# Get the Claude Code project path
PROJECT_PATH="$1"

# Log file location
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Create log file if it doesn't exist
touch "$LOG_FILE"

# Function to log blocked commands
log_blocked() {
    local command="$1"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$timestamp|$command|$PROJECT_PATH" >> "$LOG_FILE"
}

# Function to check for destructive patterns
is_destructive() {
    local command="$1"
    
    # Check for rm -rf pattern
    if [[ "$command" == *"rm -rf"* ]]; then
        log_blocked "$command"
        echo "BLOCKED: Dangerous 'rm -rf' command detected. This command has been blocked for your safety."
        return 0
    fi
    
    # Check for DROP TABLE pattern
    if [[ "$command" =~ [Dd][Rr][Oo][Pp][[:space:]]+[Tt][Aa][Bb][Ll][Ee] ]]; then
        log_blocked "$command"
        echo "BLOCKED: DROP TABLE command detected. This command has been blocked for your safety."
        return 0
    fi
    
    # Check for git push --force pattern
    if [[ "$command" == *"git push --force"* ]]; then
        log_blocked "$command"
        echo "BLOCKED: Dangerous 'git push --force' command detected. This command has been blocked for your safety."
        return 0
    fi
    
    # Check for TRUNCATE pattern
    if [[ "$command" =~ [Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee] ]]; then
        log_blocked "$command"
        echo "BLOCKED: TRUNCATE command detected. This command has been blocked for your safety."
        return 0
    fi
    
    # Check for DELETE FROM without WHERE clause
    if [[ "$command" =~ [Dd][Ee][Ll][Ee][Tt][Ee][[:space:]]+[Ff][Rr][Oo][Mm] ]]; then
        # Check if it does NOT contain WHERE clause
        if ! [[ "$command" =~ [Ww][Hh][Ee][Rr][Ee] ]]; then
            log_blocked "$command"
            echo "BLOCKED: DELETE FROM command without WHERE clause detected. This command has been blocked for your safety."
            return 0
        fi
    fi
    
    return 1
}

# Main execution
if [ -n "$PROJECT_PATH" ] && [ -n "$1" ]; then
    # Read the command from stdin
    COMMAND=$(cat)
    
    # Check if command is destructive
    if is_destructive "$COMMAND"; then
        exit 1
    fi
    
    # If we get here, command is safe - allow it to proceed
    echo "$COMMAND"
    exit 0
else
    # If no project path, just pass through
    cat
    exit 0
fi