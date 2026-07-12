#!/bin/bash

# Claude Code pre-tool-use hook to block destructive bash commands
# Installation: Place in ~/.claude/hooks/pre-tool-use.block-destructive-commands.sh
# Make executable: chmod +x ~/.claude/hooks/pre-tool-use.block-destructive-commands.sh

set -euo pipefail

# Get the command from Claude's tool input
COMMAND="$(cat)"

# Get project path from environment variable or default to current directory
PROJECT_PATH="${CLAUDE_PROJECT_PATH:-$(pwd)}"

# Function to log blocked attempts
log_blocked() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$timestamp | $COMMAND | $PROJECT_PATH" >> ~/.claude/hooks/blocked.log 2>/dev/null || echo "$timestamp | $COMMAND | $PROJECT_PATH" >> /tmp/claude-blocked.log
}

# List of blocked patterns
BLOCKED_PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "git push --force"
    "TRUNCATE"
    "DELETE FROM[^;]*;"
)

# Check if command contains any blocked patterns
is_blocked() {
    for pattern in "${BLOCKED_PATTERNS[@]}"; do
        if echo "$COMMAND" | grep -E -q "^$pattern" ; then
            # Special case for DELETE FROM without WHERE
            if [[ "$pattern" == "DELETE FROM[^;]*;" ]]; then
                # Check if it has a WHERE clause
                if ! echo "$COMMAND" | grep -i -q "where"; then
                    return 0
                fi
            else
                return 0
            fi
        fi
    done
    return 1
}

# Block destructive commands
if is_blocked; then
    log_blocked
    echo "ERROR: Blocked potentially destructive command: $COMMAND" >&2
    echo "Reason: Command contains a blocked pattern (rm -rf, DROP TABLE, etc.)" >&2
    echo "Project: $PROJECT_PATH" >&2
    echo "For more information, check the hook documentation." >&2
    exit 1
fi

# If we get here, the command is allowed
echo "$COMMAND"