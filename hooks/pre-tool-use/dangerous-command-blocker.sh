#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Dangerous Command Blocker
# Blocks destructive bash commands before execution
# Install: cp to ~/.claude/hooks/ and configure in settings

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="${PWD}"

# Read the tool input from stdin (JSON)
INPUT=$(cat)

# Extract the tool name and command
TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")

# Only check bash/shell tool calls
if [[ "$TOOL_NAME" != "bash" && "$TOOL_NAME" != "shell" && "$TOOL_NAME" != "Bash" ]]; then
    # Not a bash command, allow it
    echo '{"decision": "approve"}'
    exit 0
fi

# Extract the command being run
COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
# Handle different input formats
cmd = d.get('tool_input', {}).get('command', '')
if not cmd:
    cmd = d.get('input', {}).get('command', '')
if not cmd:
    cmd = d.get('command', '')
print(cmd)
" 2>/dev/null || echo "")

if [[ -z "$COMMAND" ]]; then
    echo '{"decision": "approve"}'
    exit 0
fi

# Define dangerous patterns
DANGEROUS_PATTERNS=(
    'rm -rf /'
    'rm -rf ~'
    'rm -rf \*'
    'rm -rf .'
    'rm -rf ..'
    'DROP TABLE'
    'DROP DATABASE'
    'TRUNCATE TABLE'
    'TRUNCATE '
    'git push --force'
    'git push -f '
    'git push origin --force'
    'chmod -R 777 /'
    'mkfs\.'
    'dd if=/dev/zero'
    ':(){ :|:& };:'
    'shutdown'
    'reboot'
    'init 0'
    'init 6'
)

# Check for DELETE FROM without WHERE clause
check_delete_without_where() {
    local cmd_upper
    cmd_upper=$(echo "$1" | tr '[:lower:]' '[:upper:]')
    if echo "$cmd_upper" | grep -qE 'DELETE\s+FROM\s+' ; then
        if ! echo "$cmd_upper" | grep -qE 'DELETE\s+FROM\s+\S+\s+WHERE\s+' ; then
            return 0  # dangerous: DELETE without WHERE
        fi
    fi
    return 1  # safe
}

# Check each dangerous pattern
BLOCKED=""
REASON=""

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qi "$pattern"; then
        BLOCKED="true"
        REASON="Matched dangerous pattern: $pattern"
        break
    fi
done

# Check DELETE without WHERE
if [[ -z "$BLOCKED" ]]; then
    if check_delete_without_where "$COMMAND"; then
        BLOCKED="true"
        REASON="DELETE FROM without WHERE clause detected"
    fi
fi

# Check for rm -rf with path that looks like root or home
if [[ -z "$BLOCKED" ]]; then
    if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?(-[a-zA-Z]*r[a-zA-Z]*\s+)?/($|\s)'; then
        BLOCKED="true"
        REASON="Recursive forced deletion of root directory"
    fi
fi

if [[ "$BLOCKED" == "true" ]]; then
    # Log the blocked attempt
    mkdir -p "$(dirname "$LOG_FILE")"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$TIMESTAMP] BLOCKED | Project: $PROJECT_PATH | Command: $COMMAND | Reason: $REASON" >> "$LOG_FILE"

    # Return block decision with explanation
    cat <<EOF
{
    "decision": "block",
    "message": "🚫 BLOCKED: This command was intercepted by the dangerous command blocker.\n\nCommand: $COMMAND\nReason: $REASON\n\nIf you believe this is a false positive, please modify the command to be more specific and safe."
}
EOF
    exit 0
fi

# Command is safe, approve
echo '{"decision": "approve"}'
