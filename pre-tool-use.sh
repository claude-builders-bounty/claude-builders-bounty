#!/bin/bash

# Claude Code Pre-Tool-Use Security Hook
# Blocks destructive commands to prevent accidental data loss.

# Configuration
LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# The command being attempted is passed as the first argument
COMMAND="$1"

# Destructive patterns to block
# 1. rm -rf (Recursive force delete)
# 2. DROP TABLE / TRUNCATE (SQL destructive)
# 3. git push --force (Overwrite remote history)
# 4. DELETE FROM without WHERE (Massive data deletion)
PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "TRUNCATE TABLE"
    "git push --force"
    "git push -f"
    "DELETE FROM .*[^WHERE]"
)

for PATTERN in "${PATTERNS[@]}"; do
    if [[ "$COMMAND" =~ $PATTERN ]]; then
        # Log the blocked attempt
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        PROJECT_PATH=$(pwd)
        echo "[$TIMESTAMP] BLOCKED: $COMMAND | PATH: $PROJECT_PATH" >> "$LOG_FILE"
        
        # Output clear message to Claude
        echo "❌ ERROR: Destructive command blocked for safety."
        echo "Attempted: $COMMAND"
        echo "Reason: This command matches a prohibited destructive pattern."
        echo "If this was intentional, please modify the command to be more specific (e.g., avoid -rf or add a WHERE clause)."
        
        # Exit with non-zero to signal the tool use should be blocked
        exit 1
    fi
done

# Allow normal commands
exit 0
