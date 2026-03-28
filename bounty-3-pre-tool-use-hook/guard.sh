#!/usr/bin/env bash
# claude-guard — Pre-tool-use hook that blocks destructive bash/SQL commands
# Install: cp guard.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/guard.sh
#
# Configure in ~/.claude/settings.json:
#   "hooks": {
#     "PreToolUse": [
#       {
#         "matcher": "Bash",
#         "hooks": [{ "type": "command", "command": "~/.claude/hooks/guard.sh" }]
#       }
#     ]
#   }

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read the hook input from stdin (JSON with tool_input.command)
INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# --- Destructive pattern definitions ---

declare -a PATTERNS=(
    # Filesystem destruction
    'rm\s+-(r|f|rf|fr)\b'
    'rm\s+--recursive'
    'rm\s+--force'
    # Git force operations
    'git\s+push\s+.*--force'
    'git\s+push\s+-f\b'
    'git\s+reset\s+--hard'
    'git\s+clean\s+-fd'
    # SQL destructive operations
    'DROP\s+(TABLE|DATABASE|SCHEMA|INDEX)'
    'TRUNCATE\s+'
    'DELETE\s+FROM\s+\S+\s*;'
    'DELETE\s+FROM\s+\S+\s*$'
    # System-level dangers
    'mkfs\.'
    'dd\s+.*of=/dev/'
    '>\s*/dev/sd'
    'chmod\s+-R\s+777\s+/'
    'chown\s+-R\s+.*\s+/'
)

declare -a DESCRIPTIONS=(
    "Recursive/force file deletion (rm -rf)"
    "Recursive file deletion (rm --recursive)"
    "Force file deletion (rm --force)"
    "Git force push"
    "Git force push (-f)"
    "Git hard reset (discards all changes)"
    "Git clean -fd (deletes untracked files)"
    "DROP TABLE/DATABASE/SCHEMA/INDEX"
    "TRUNCATE (deletes all rows)"
    "DELETE FROM without WHERE clause"
    "DELETE FROM without WHERE clause"
    "Filesystem format (mkfs)"
    "Raw disk write (dd to device)"
    "Raw device overwrite"
    "Recursive chmod 777 on root"
    "Recursive chown on root"
)

# --- Check command against patterns ---

BLOCKED=""
REASON=""

for i in "${!PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qEi "${PATTERNS[$i]}"; then
        BLOCKED="true"
        REASON="${DESCRIPTIONS[$i]}"
        break
    fi
done

# --- Special case: DELETE FROM with WHERE is allowed ---

if [[ -n "$BLOCKED" ]] && echo "$COMMAND" | grep -qEi 'DELETE\s+FROM'; then
    if echo "$COMMAND" | grep -qEi 'DELETE\s+FROM\s+\S+\s+WHERE\s+'; then
        BLOCKED=""
        REASON=""
    fi
fi

# --- Output result ---

if [[ -n "$BLOCKED" ]]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    PROJECT_PATH=$(pwd)

    # Log the blocked attempt
    echo "[$TIMESTAMP] BLOCKED | reason: $REASON | command: $COMMAND | path: $PROJECT_PATH" >> "$LOG_FILE"

    # Return block decision to Claude Code (exit 2 = block)
    cat <<EOF
{"decision": "block", "reason": "BLOCKED by claude-guard: $REASON. The command '$COMMAND' was intercepted because it matches a destructive pattern. If you need to perform this operation, ask the user for explicit confirmation first."}
EOF
    exit 2
fi

# Allow the command (exit 0 = allow)
exit 0
