#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
# Blocks dangerous patterns before execution, logs attempts, and explains why.
#
# Installation:
#   mkdir -p ~/.claude/hooks && cp this-file ~/.claude/hooks/pre-tool-use-block-destructive.sh && chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.sh
#   # Add to .claude/settings.json: { "hooks": { "PreToolUse": [{ "type": "command", "command": "bash ~/.claude/hooks/pre-tool-use-block-destructive.sh" }] } }

set -euo pipefail

# Read the tool input from stdin (Claude Code hooks receive JSON on stdin)
INPUT=$(cat)

# Extract the command being executed (for bash tool)
COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    # Claude Code sends tool_use with name and input
    tool_name = data.get('tool_name', data.get('name', ''))
    tool_input = data.get('tool_input', data.get('input', {}))
    if tool_name == 'Bash' or tool_name == 'bash':
        print(tool_input.get('command', ''))
    else:
        print('')
except:
    print('')
" 2>/dev/null || true)

# If no command (not a bash tool), allow it through
if [ -z "$COMMAND" ]; then
    echo "$INPUT"
    exit 0
fi

# Define dangerous patterns (regex)
DANGEROUS_PATTERNS=(
    # Destructive file operations
    'rm\s+-rf?\s+[^/]'
    'rm\s+-rf?\s+~'
    'rm\s+-rf?\s+/\w'
    'rm\s+-rf?\s+\*'
    # Database destruction
    '[Dd][Rr][Oo][P]\s+[Tt][Aa][Bb][Ll][Ee]'
    '[Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee]'
    '[Dd][Ee][Ll][Ee][Tt][Ee]\s+[Ff][Rr][Oo][Mm](?!\s+[Ww][Hh][Ee][Rr][Ee])'
    # Git force push
    '[Gg][Ii][Tt]\s+(push|upload).*--force'
    '[Gg][Ii][Tt]\s+push.*-[fF]'
    # Disk wiping
    'dd\s+if=/dev/zero'
    'mkfs\.\w+'
    '> /dev/sd[a-z]'
    'chmod\s+-R\s+777\s+/'
)

BLOCKED=false
MATCHED_PATTERN=""

for PATTERN in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qP "$PATTERN" 2>/dev/null; then
        BLOCKED=true
        MATCHED_PATTERN="$PATTERN"
        break
    fi
done

if [ "$BLOCKED" = true ]; then
    # Log the blocked attempt
    LOG_DIR="$HOME/.claude/hooks"
    mkdir -p "$LOG_DIR"
    TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    PROJECT_PATH="${PWD:-unknown}"
    
    echo "[${TIMESTAMP}] command=\"${COMMAND}\" pattern=\"${MATCHED_PATTERN}\" path=\"${PROJECT_PATH}\"" >> "${LOG_DIR}/blocked.log"
    
    # Output the block message for Claude (this replaces the tool result)
    python3 -c "
import json, sys
print(json.dumps({
    'decision': 'block',
    'reason': f'⛔ Command blocked by safety hook: matched dangerous pattern \"{sys.argv[1]}\".\n\nThe following command was intercepted before execution:\n\`\`\`bash\n{sys.argv[2]}\n\`\`\`\n\nThis pattern can cause irreversible data loss. If you truly need to run this command, ask the user for explicit confirmation first, then retry with a safer alternative (e.g., add --interactive flags, use dry-run mode, or target specific files instead of wildcards).',
    'tool_result': {'type': 'error', 'content': f'Safety hook blocked destructive command (pattern: {sys.argv[1]})'}
}))
" "$MATCHED_PATTERN" "$COMMAND"
    
    exit 0
fi

# Not blocked — pass through the original input unchanged
echo "$INPUT"
exit 0
