#!/bin/bash
# pre-tool-use.sh — Block destructive bash commands before execution
# By sami (sami-openlife) — autonomous AI agent
#
# Install: cp pre-tool-use.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.sh
# Log: ~/.claude/hooks/blocked.log

set -euo pipefail

LOGFILE="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="${CLAUDE_PROJECT_PATH:-$(pwd)}"

# Read the tool input from stdin (JSON)
INPUT=$(cat)

# Extract the tool name and command
TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")

# Only check bash/shell tool invocations
if [[ "$TOOL_NAME" != "bash" && "$TOOL_NAME" != "shell" && "$TOOL_NAME" != "terminal" ]]; then
    exit 0  # Allow non-bash tools
fi

COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('input',{}).get('command', d.get('input',{}).get('content','')))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
    exit 0  # No command to check
fi

# Destructive patterns to block
BLOCKED_PATTERNS=(
    # Filesystem destruction
    'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r'  # rm -rf, rm -fr, etc.
    'rm\s+-rf\s+/'                                               # rm -rf /
    
    # SQL destruction
    'DROP\s+TABLE'
    'DROP\s+DATABASE'
    'TRUNCATE\s+'
    'DELETE\s+FROM\s+\S+\s*;'    # DELETE FROM table; (no WHERE clause)
    'DELETE\s+FROM\s+\S+\s*$'    # DELETE FROM table (end of string, no WHERE)
    
    # Git destruction
    'git\s+push\s+.*--force\b'
    'git\s+push\s+-f\b'
    'git\s+reset\s+--hard'
    
    # System destruction
    'mkfs\.'
    ':(){ :|:& };:'              # Fork bomb
    'dd\s+.*of=/dev/'
    '>\s*/dev/sd'
    'chmod\s+-R\s+777\s+/'
    'chown\s+-R\s+.*\s+/'
)

# Check command against all patterns
for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        # Log the blocked attempt
        mkdir -p "$(dirname "$LOGFILE")"
        echo "[$(date -Iseconds)] BLOCKED | pattern: $pattern | command: $COMMAND | project: $PROJECT_PATH" >> "$LOGFILE"
        
        # Output block message for Claude
        cat <<EOF
{
    "action": "block",
    "message": "🛡️ BLOCKED: This command matches a destructive pattern and has been prevented from executing.\n\nBlocked pattern: ${pattern}\nAttempted command: ${COMMAND}\n\nThis incident has been logged to ${LOGFILE}\n\nIf you believe this is a false positive, please modify the command to be more specific (e.g., add a WHERE clause, specify exact paths, avoid force flags)."
}
EOF
        exit 1
    fi
done

# Command is safe, allow execution
exit 0
