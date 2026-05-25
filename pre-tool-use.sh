#!/usr/bin/env bash
# pre-tool-use hook - Blocks dangerous bash commands
# Install: cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use

set -e

LOG_FILE="$HOME/.claude/hooks/blocked.log"
COMMAND="${CLAUDE_TOOL_INPUT:-$*}"

# Patterns to block (case-insensitive)
BLOCKED_PATTERNS=(
    "rm[[:space:]]+-rf[[:space:]]+/"
    "rm[[:space:]]+-rf[[:space:]]+--no-preserve-root"
    "DROP[[:space:]]+TABLE"
    "TRUNCATE[[:space:]]+TABLE"
    "git[[:space:]]+push[[:space:]]+--force"
    "git[[:space:]]+push[[:space:]]+-f[[:space:]]+origin[[:space:]]+.*:"
    "DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_]+[[:space:]]*(?!WHERE)"
    "mkfs\."
    "dd[[:space:]]+if="
    ">\s+/dev/"
    ":(){[[:space:]]*:|:&};:"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        PROJECT_PATH="${PWD:-unknown}"
        
        # Log the blocked attempt
        mkdir -p "$(dirname "$LOG_FILE")"
        echo "[$TIMESTAMP] BLOCKED | project=$PROJECT_PATH | command=$COMMAND" >> "$LOG_FILE"
        
        # Display clear message to Claude
        cat <<EOF
⚠️  DESTRUCTIVE COMMAND BLOCKED by pre-tool-use hook

Pattern matched: $(echo "$COMMAND" | grep -ioE "$pattern")
Attempted command: $COMMAND

This command has been blocked because it matches a dangerous pattern.
If you are sure this is safe, re-run with: BLOCKING_OVERRIDE=1 <command>

Logged to: $LOG_FILE
EOF
        exit 1
    fi
done

exit 0
