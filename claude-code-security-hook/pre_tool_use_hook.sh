#!/bin/bash
#
# Claude Code Pre-Tool-Use Security Hook (Bash Version)
# 
# Place this in ~/.claude/hooks/pre_tool_use.sh
# Make executable: chmod +x ~/.claude/hooks/pre_tool_use.sh
#

LOG_DIR="$HOME/.claude/hooks"
LOG_FILE="$LOG_DIR/blocked.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Read stdin (Claude Code passes tool use request)
INPUT=$(cat)

# Extract command from JSON (simple grep-based extraction)
COMMAND=$(echo "$INPUT" | grep -oP '"command"\s*:\s*"\K[^"]+' | head -1)

if [ -z "$COMMAND" ]; then
    exit 0  # No command found, allow
fi

# Check for dangerous patterns
DANGEROUS=0
REASON=""

# rm -rf patterns
if echo "$COMMAND" | grep -qiE 'rm\s+(-[rf]+\s+)*(/\s*|~/\s*|\*\s*)'; then
    DANGEROUS=1
    REASON="DANGEROUS_RM: Attempt to remove root/home directory"
elif echo "$COMMAND" | grep -qiE 'rm\s+(-[rf]+\s+)+'; then
    DANGEROUS=1
    REASON="DANGEROUS_RM: Recursive force delete detected"
fi

# SQL patterns
if echo "$COMMAND" | grep -qiE 'DROP\s+TABLE\s+'; then
    DANGEROUS=1
    REASON="DANGEROUS_SQL: DROP TABLE detected"
elif echo "$COMMAND" | grep -qiE 'DELETE\s+FROM.*WHERE\s+1\s*=\s*1'; then
    DANGEROUS=1
    REASON="DANGEROUS_SQL: Mass DELETE detected"
elif echo "$COMMAND" | grep -qiE 'TRUNCATE\s+(TABLE\s+)?'; then
    DANGEROUS=1
    REASON="DANGEROUS_SQL: TRUNCATE detected"
fi

# Permission patterns
if echo "$COMMAND" | grep -qiE 'chmod\s+(-R\s+)?777'; then
    DANGEROUS=1
    REASON="DANGEROUS_PERM: Setting world-writable permissions"
fi

# Disk destruction
if echo "$COMMAND" | grep -qiE 'dd\s+if=/dev/zero'; then
    DANGEROUS=1
    REASON="DANGEROUS_DISK: Disk zeroing detected"
fi

# Fork bombs
if echo "$COMMAND" | grep -qE ':\(\)\{.*:\|:&.*\}'; then
    DANGEROUS=1
    REASON="DANGEROUS_FORK: Fork bomb detected"
fi

# Remote code execution
if echo "$COMMAND" | grep -qiE 'curl\s+.*\|\s*(ba)?sh'; then
    DANGEROUS=1
    REASON="DANGEROUS_RCE: Curl piped to shell"
elif echo "$COMMAND" | grep -qiE 'wget\s+.*\|\s*(ba)?sh'; then
    DANGEROUS=1
    REASON="DANGEROUS_RCE: Wget piped to shell"
fi

# Block if dangerous
if [ $DANGEROUS -eq 1 ]; then
    TIMESTAMP=$(date -Iseconds)
    echo "[$TIMESTAMP] BLOCKED: $REASON" >> "$LOG_FILE"
    echo "  Command: $COMMAND" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    echo "🚫 BLOCKED: $REASON" >&2
    echo "   Command: $COMMAND" >&2
    echo "   Logged to: $LOG_FILE" >&2
    
    exit 1
fi

# Command is safe
exit 0
