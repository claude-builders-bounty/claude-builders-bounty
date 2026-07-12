#!/bin/bash

# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
# This hook intercepts dangerous bash commands and blocks them for safety

set -euo pipefail

# Configuration
HOOKS_DIR="$HOME/.claude/hooks"
LOG_FILE="$HOOKS_DIR/blocked.log"

# Ensure log file exists
mkdir -p "$HOOKS_DIR"
touch "$LOG_FILE"

# Function to log blocked commands
log_blocked_command() {
    local timestamp="$1"
    local command="$2"
    local project_path="$3"
    echo "[$timestamp] Blocked command: $command (Project: $project_path)" >> "$LOG_FILE"
}

# Read input from Claude Code
INPUT=$(cat)

# Parse the input JSON
PROJECT_PATH=$(echo "$INPUT" | jq -r '.project_path // empty')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT" | jq -r '.command // empty' | xargs)

# If not a bash command tool use, pass through
if [[ "$TOOL_NAME" != "bash" ]]; then
    echo "$INPUT"
    exit 0
fi

# Check for destructive command patterns
BLOCKED=0
BLOCKED_REASON=""

# Check for dangerous patterns
if [[ "$COMMAND" == *"rm -rf"* ]]; then
    BLOCKED=1
    BLOCKED_REASON="Blocked rm -rf command"
elif [[ "$COMMAND" == *"DROP TABLE"* ]]; then
    BLOCKED=1
    BLOCKED_REASON="Blocked DROP TABLE command"
elif [[ "$COMMAND" == *"git push --force"* ]]; then
    BLOCKED=1
    BLOCKED_REASON="Blocked git push --force command"
elif [[ "$COMMAND" == *"TRUNCATE"* ]]; then
    BLOCKED=1
    BLOCKED_REASON="Blocked TRUNCATE command"
elif [[ "$COMMAND" == *"DELETE FROM"* ]] && ! [[ "$COMMAND" == *"WHERE"* ]]; then
    BLOCKED=1
    BLOCKED_REASON="Blocked DELETE FROM command without WHERE clause"
fi

# If a destructive command was detected, block it
if [ $BLOCKED -eq 1 ]; then
    TIMESTAMP=$(date -Iseconds)
    log_blocked_command "$TIMESTAMP" "$COMMAND" "$PROJECT_PATH"
    
    # Output to Claude explaining why the command was blocked
    echo "{
  \"error\": \"BLOCKED_COMMAND\",
  \"message\": \"$BLOCKED_REASON\",
  \"command\": \"$COMMAND\"
}"
    exit 1
fi

# If we get here, it's a safe command, so pass the original input through
echo "$INPUT"
exit 0