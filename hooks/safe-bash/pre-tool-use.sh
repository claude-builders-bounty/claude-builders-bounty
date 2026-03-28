#!/bin/bash

# Extract the tool name and tool inputs from standard input (provided by Claude Code)
PAYLOAD=$(cat -)
TOOL_NAME=$(echo "$PAYLOAD" | jq -r '.tool_name')

# We only care about the Bash tool
if [ "$TOOL_NAME" != "Bash" ]; then
    echo "{\"status\": \"approved\"}"
    exit 0
fi

COMMAND=$(echo "$PAYLOAD" | jq -r '.tool_input.command')

# List of dangerous patterns
PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "git push --force"
    "git push -f"
    "TRUNCATE"
)

BLOCKED=false

for PATTERN in "${PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -iq "$PATTERN"; then
        BLOCKED=true
        break
    fi
done

# Special case for DELETE FROM without WHERE
if echo "$COMMAND" | grep -iq "DELETE FROM" && ! echo "$COMMAND" | grep -iq "WHERE"; then
    BLOCKED=true
fi

if [ "$BLOCKED" = true ]; then
    # Log the blocked attempt
    LOG_DIR="$HOME/.claude/hooks"
    mkdir -p "$LOG_DIR"
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    PROJECT_PATH=$(pwd)
    echo "[$TIMESTAMP] BLOCKED: '$COMMAND' in $PROJECT_PATH" >> "$LOG_DIR/blocked.log"

    # Reject the tool use
    echo "{\"status\": \"rejected\", \"message\": \"The command '$COMMAND' was blocked because it contains a potentially destructive pattern (e.g., rm -rf, DROP, TRUNCATE, or DELETE without WHERE). Please rethink your approach or ask the user to run it manually.\"}"
    exit 0
fi

# If safe, approve
echo "{\"status\": \"approved\"}"
