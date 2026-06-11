#!/bin/bash
# Pre-tool-use hook that blocks destructive bash commands
# Claude Code Hooks Format

# Blocked patterns
BLOCKED_PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "git push --force"
    "TRUNCATE"
    "DELETE FROM"
)

# Log file
LOG_DIR="$HOME/.claude/hooks"
LOG_FILE="$LOG_DIR/blocked.log"
mkdir -p "$LOG_DIR"

# Check command
for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$CLAUDE_CODE_COMMAND" | grep -qi "$pattern"; then
        # Log the attempt
        echo "$(date '+%Y-%m-%d %H:%M:%S') | Command: $CLAUDE_CODE_COMMAND | Project: $PWD" >> "$LOG_FILE"
        echo "❌ BLOCKED: Command contains '$pattern' - dangerous operation detected"
        exit 1
    fi
done

# Allow normal commands
exit 0
