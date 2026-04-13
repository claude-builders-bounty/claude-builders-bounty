#!/bin/bash

# Michael Sovereign V7.0.0 — Claude Code Safety Guard
# [BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands

COMMAND="$1"
PROJECT_PATH=$(pwd)
LOG_FILE="$HOME/.claude/hooks/blocked.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Dangerous patterns
declare -a PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "git push --force"
    "TRUNCATE"
    "DELETE FROM"
)

# Function to block and log
block_command() {
    local pattern="$1"
    echo "$TIMESTAMP | BLOCKED: $COMMAND | PATTERN: $pattern | PATH: $PROJECT_PATH" >> "$LOG_FILE"
    echo "❌ SECURITY ALERT: The command you are trying to execute matches a destructive pattern ($pattern) and has been blocked by the Michael Sovereign Safety Hook."
    echo "Please refine your command to avoid accidental data loss or force-pushing to the repository."
    exit 1
}

# Special check for DELETE FROM without WHERE
if [[ "$COMMAND" == *"DELETE FROM"* ]] && [[ "$COMMAND" != *"WHERE"* ]]; then
    block_command "DELETE FROM without WHERE"
fi

# Check other patterns
for pattern in "${PATTERNS[@]}"; do
    if [[ "$COMMAND" == *"$pattern"* ]]; then
        block_command "$pattern"
    fi
done

# If no matches, exit 0 to allow execution
exit 0
