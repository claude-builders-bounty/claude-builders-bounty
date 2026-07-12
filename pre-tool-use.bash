#!/bin/bash

# Claude Code hook for blocking destructive bash commands
# 
# Installation:
#   mkdir -p ~/.claude/hooks
#   cp this file to ~/.claude/hooks/pre-tool-use.bash

set -euo pipefail

# Log file for blocked commands
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Ensure log file exists
touch "$LOG_FILE"

# Function to log blocked commands
log_blocked() {
    local timestamp=$(date -Iseconds)
    local command="$1"
    local project_path="$2"
    echo "[$timestamp] BLOCKED: $command (Project: $project_path)" >> "$LOG_FILE"
}

# Get the command from Claude (passed as arguments to this script)
CLAUDE_COMMAND="$*"

# Get project path from environment variable or default to current directory
PROJECT_PATH="${CLAUDE_PROJECT_PATH:-$(pwd)}"

# Destructive patterns to block
DESTRUCTIVE_PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "git push --force"
    "TRUNCATE"
)

# Check for DELETE FROM without WHERE clause
if [[ $CLAUDE_COMMAND == "DELETE FROM"* ]] && [[ $CLAUDE_COMMAND != *"WHERE"* ]]; then
    log_blocked "$CLAUDE_COMMAND" "$PROJECT_PATH"
    echo "BLOCKED: Destructive command detected: $CLAUDE_COMMAND"
    echo "Reason: DELETE FROM without WHERE clause is destructive"
    exit 1
fi

# Check for other destructive patterns
for pattern in "${DESTRUCTIVE_PATTERNS[@]}"; do
    if [[ $CLAUDE_COMMAND == *"$pattern"* ]]; then
        log_blocked "$CLAUDE_COMMAND" "$PROJECT_PATH"
        echo "BLOCKED: Destructive command detected: $pattern"
        exit 1
    fi
done