#!/usr/bin/env bash
# pre-tool-use hook for Claude Code (bash variant)
# Blocks dangerous bash commands before execution.
# Place in ~/.claude/hooks/pre-tool-use
#
# This is a simpler alternative to the Python version.
# The Python version is preferred for richer logging.

BLOCKED_LOG="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$BLOCKED_LOG")"

# Read the command from Claude Code's arguments
TOOL_NAME="$1"
TOOL_INPUT="$2"

# Only check bash commands
if [ "$TOOL_NAME" != "bash" ] && [ "$TOOL_NAME" != "execute_command" ]; then
    exit 0
fi

# Extract command string from JSON input
COMMAND=$(echo "$TOOL_INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('command','') or d.get('cmd','') or '')" 2>/dev/null)
[ -z "$COMMAND" ] && exit 0

# Check for dangerous patterns
DANGEROUS=0

echo "$COMMAND" | grep -qiE '\brm\s+-rf\b' && DANGEROUS=1
echo "$COMMAND" | grep -qiE '\bDROP\s+TABLE\b' && DANGEROUS=1
echo "$COMMAND" | grep -qiE '\bgit\s+push\s+--force\b' && DANGEROUS=1
echo "$COMMAND" | grep -qiE '\bTRUNCATE\b' && DANGEROUS=1
echo "$COMMAND" | grep -qiE '\bDELETE\s+FROM\b' && DANGEROUS=1
echo "$COMMAND" | grep -qiE '\bsudo\s+rm\b' && DANGEROUS=1
echo "$COMMAND" | grep -qiE '\bchmod\s+-R\s+777\b' && DANGEROUS=1

if [ "$DANGEROUS" = "1" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | $COMMAND | $(pwd)" >> "$BLOCKED_LOG"
    echo ""
    echo "⚠️  BLOCKED: Destructive command detected and prevented."
    echo "   Command: ${COMMAND:0:200}"
    echo "   Reason: Matched a dangerous security pattern."
    echo "   Logged to: $BLOCKED_LOG"
    echo ""
    exit 1
fi

exit 0
