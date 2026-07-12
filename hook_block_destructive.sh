#!/bin/bash

# Hook to block destructive commands in Claude Code

# Check if TOOL_NAME and TOOL_INPUT are set (indicating this is being called as a hook)
if [ -n "$TOOL_NAME" ] && [ "$TOOL_NAME" == "bash" ]; then
    # Extract command from input
    COMMAND="$TOOL_INPUT"
    
    # List of destructive patterns to block
    DESTRUCTIVE_PATTERNS=(
        "rm -rf"
        "DROP TABLE"
        "git push --force"
        "TRUNCATE"
        "DELETE FROM[^[:alpha:]]*[^[:space:]]*$"  # DELETE FROM without WHERE
    )
    
    # Check each pattern
    for pattern in "${DESTRUCTIVE_PATTERNS[@]}"; do
        if [[ $COMMAND =~ $pattern ]]; then
            # Log the blocked command
            TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            LOG_FILE="$HOME/.claude/hooks/blocked.log"
            PROJECT_PATH=$(pwd)
            
            # Create log entry
            echo "$TIMESTAMP | BLOCKED: $COMMAND | PROJECT: $PROJECT_PATH" >> "$LOG_FILE"
            
            # Output error message to Claude
            echo "ERROR: Destructive command blocked: $pattern"
            echo "The following command was blocked due to security policy:"
            echo "$COMMAND"
            echo ""
            echo "This command has been blocked to prevent potential data loss."
            echo "Blocked commands are logged in $LOG_FILE"
            exit 1
        fi
    done
    
    # If we get here, the command is allowed
    echo "$COMMAND" # Output the command to allow execution
    
elif [ -n "$TOOL_NAME" ]; then
    # For other tools, just pass through
    echo "$COMMAND"
else
    # Not being called as a hook, so just execute the command
    if [ -n "$COMMAND" ]; then
        eval "$COMMAND"
    fi
fi

# Log file location
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Create the log file if it doesn't exist
touch "$LOG_FILE"

# Make the hooks directory if it doesn't exist
mkdir -p "$HOME/.claude/hooks/"