#!/bin/bash
# Pre-tool-use hook that blocks destructive bash commands
# Claude Code Hooks Format

BLOCKED_PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "git push --force"
    "TRUNCATE"
    "DELETE FROM"
)

# Log directory
LOG_DIR="$HOME/.claude/hooks"
LOG_FILE="$LOG_DIR/blocked.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check command against blocked patterns
for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$CLAUDE_CODE_COMMAND" | grep -qi "$pattern"; then
        # Log the blocked attempt
        echo "$(date '+%Y-%m-%d %H:%M:%S') | Command: $CLAUDE_CODE_COMMAND | Project: $PWD" >> "$LOG_FILE"
        
        # Display clear message
        echo "❌ BLOCKED: Command '$CLAUDE_CODE_COMMAND' contains dangerous pattern '$pattern'"
        echo "   This command has been logged to $LOG_FILE"
        exit 1
    fi
done

# Allow normal commands to proceed
exit 0
