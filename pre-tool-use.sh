#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Block Destructive Commands
# Place this file at: ~/.claude/hooks/pre-tool-use.sh
#
# Installation:
#   1. mkdir -p ~/.claude/hooks
#   2. cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh

BLOCKED_LOG="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$BLOCKED_LOG")"

# Patterns to block
DANGEROUS_PATTERNS=(
    "rm -rf"
    "rm -fr"
    "DROP TABLE"
    "TRUNCATE"
    "git push --force"
    "git push -f"
    "DELETE FROM"
)

BLOCKED_MSG="🚫 BLOCKED: This command matches a dangerous pattern and was intercepted for safety.

Blocked patterns:
${DANGEROUS_PATTERNS[*]}

If this was intentional, you can bypass by:
1. Removing the dangerous argument (recommended)
2. Using a safer alternative (e.g., 'trash-cli' instead of 'rm -rf')
3. Adding explicit confirmation prompts

Project: $(pwd)
Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# Check if the command contains any dangerous patterns
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    # Case-insensitive check
    if echo "$CLAUDE_CODE_COMMAND" | grep -iq "$pattern"; then
        # Log the blocked attempt
        echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] BLOCKED: '$CLAUDE_CODE_COMMAND' | Project: $(pwd)" >> "$BLOCKED_LOG"
        
        # Return the block message
        echo "$BLOCKED_MSG"
        exit 1
    fi
done

# Command is safe - continue normally
exit 0
