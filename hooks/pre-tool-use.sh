#!/bin/bash

# Claude Code Pre-Tool-Use Security Hook
# Objective: Intercept and block destructive commands.
# Reward: 00 USD (Opire)

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

COMMAND="$1"
PROJECT_PATH="$(pwd)"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# destructive patterns
PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "git push --force"
    "TRUNCATE"
    "DELETE FROM"
)

for pattern in "${PATTERNS[@]}"; do
    if [[ "$COMMAND" == *"$pattern"* ]]; then
        # Check for DELETE FROM without WHERE (simple regex)
        if [[ "$pattern" == "DELETE FROM" ]] && [[ ! "$COMMAND" == *"WHERE"* ]]; then
            : # Blocked
        elif [[ "$pattern" == "DELETE FROM" ]]; then
            continue # Safe with WHERE clause
        fi

        echo "🚨 SECURITY ALERT: Destructive command detected!"
        echo "Command: $COMMAND"
        echo "Reason: Matches blocked pattern '$pattern'"
        
        # Log the attempt
        echo "[$TIMESTAMP] BLOCKED: '$COMMAND' | PATH: $PROJECT_PATH" >> "$LOG_FILE"
        
        exit 1
    fi
done

exit 0
