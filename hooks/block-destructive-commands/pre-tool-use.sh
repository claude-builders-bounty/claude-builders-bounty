#!/bin/bash

# Pre-tool-use hook to block destructive bash commands
INPUT=$(cat)

BLOCKED=0
REASON=""

if echo "$INPUT" | grep -q 'rm -rf'; then
    BLOCKED=1
    REASON="rm -rf pattern detected"
elif echo "$INPUT" | grep -qi 'DROP TABLE'; then
    BLOCKED=1
    REASON="DROP TABLE pattern detected"
elif echo "$INPUT" | grep -q 'git push --force'; then
    BLOCKED=1
    REASON="git push --force pattern detected"
elif echo "$INPUT" | grep -qi 'TRUNCATE'; then
    BLOCKED=1
    REASON="TRUNCATE pattern detected"
elif echo "$INPUT" | grep -qi 'DELETE FROM'; then
    if ! echo "$INPUT" | grep -qi 'WHERE'; then
        BLOCKED=1
        REASON="DELETE FROM without WHERE clause detected"
    fi
fi

if [ "$BLOCKED" -eq 1 ]; then
    LOG_FILE="$HOME/.claude/hooks/blocked.log"
    mkdir -p "$(dirname "$LOG_FILE")"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    PROJECT_PATH=$(pwd)
    
    # Extract just the command part roughly for the log, or log the whole input
    # As input is JSON, we'll log the reason to be safe
    echo "[$TIMESTAMP] Project: $PROJECT_PATH | Blocked Reason: $REASON" >> "$LOG_FILE"
    
    # Provide a clear message to Claude
    echo "SECURITY HOOK TRIGGERED: The command was blocked."
    echo "Reason: $REASON"
    echo "Please use a safer alternative to accomplish this task."
    exit 1
fi

echo "$INPUT"
exit 0
