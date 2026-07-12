#!/bin/bash

# pre-tool-use hook that blocks destructive bash commands
# Save as ~/.claude/hooks/pre-tool-use-blocker.sh

set -euo pipefail

# Log file location
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# List of destructive patterns to block
declare -A BLOCKED_PATTERNS=(
    ["rm -rf"]="File deletion with rm -rf is blocked for safety"
    ["DROP TABLE"]="SQL DROP TABLE commands are blocked"
    ["git push --force"]="Force push is blocked to prevent history rewrites"
    ["TRUNCATE"]="SQL TRUNCATE commands are blocked"
    ["DELETE FROM"]="Unconditional SQL DELETE commands are blocked"
)

# Function to check if command should be blocked
should_block_command() {
    local command="$1"
    
    for pattern in "${!BLOCKED_PATTERNS[@]}"; do
        if [[ $command == *"$pattern"* ]]; then
            # Special handling for DELETE FROM without WHERE clause
            if [[ "$pattern" == "DELETE FROM" ]] && [[ ! "$command" =~ WHERE ]]; then
                return 0
            elif [[ "$pattern" != "DELETE FROM" ]]; then
                return 0
            fi
        fi
    done
    return 1
}

# Main execution
if should_block_command "$*"; then
    echo "$(date): Blocked command: $* in project: $PWD" >> "$LOG_FILE"
    echo "❌ Blocked potentially destructive command: $*"
    echo "Reason: ${BLOCKED_PATTERITS[$command]}"
    exit 1
fi

# Allow non-blocked commands to proceed normally
exec "$@"