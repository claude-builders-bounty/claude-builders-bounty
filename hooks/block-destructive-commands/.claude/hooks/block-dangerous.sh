#!/usr/bin/env bash
# block-dangerous.sh — PreToolUse hook for Claude Code
# Blocks dangerous bash commands like rm -rf, DROP TABLE, git push --force
# Installation: cp this file to ~/.claude/hooks/block-dangerous.sh
set -euo pipefail

INPUT_FILE="${1:-/dev/stdin}"
LOG_FILE="${CLAUDE_HOOKS_DIR:-$HOME/.claude/hooks}/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read JSON input from stdin
INPUT=$(cat "$INPUT_FILE")

# Extract tool name and command
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_name', ''))
except:
    print('')
" 2>/dev/null || echo "")

# Only intercept Bash tool
if [ "$TOOL_NAME" != "Bash" ] && [ "$TOOL_NAME" != "bash" ]; then
    exit 0
fi

# Extract the command
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    ti = data.get('tool_input', {})
    print(ti.get('command', ti.get('cmd', '')))
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
    exit 0
fi

# ─── Danger Patterns ─────────────────────────────────────────────────────
# Each entry: pattern|description
DANGEROUS_PATTERNS=$(cat << 'EOF'
rm\s+.*-[a-zA-Z]*[rR][a-zA-Z]*[fF]|Recursive force delete (rm -rf) — permanently deletes files without confirmation
sudo\s+rm|Sudo delete — bypasses filesystem protections
>\s+/dev/sda|Direct disk write — can corrupt the entire filesystem
mkfs\.|Filesystem format — destroys all data on a partition
dd\s+if=|Raw disk write — can overwrite boot sectors and partitions
git\s+push\s+--force|Force push — overwrites remote branch history, can destroy teammates' work
git\s+push\s+-f\b|Force push (short flag) — same as --force
DROP\s+(TABLE|DATABASE|SCHEMA)|DROP statement — permanently deletes database structure
TRUNCATE\s+|TRUNCATE statement — rapidly deletes all rows without transaction safety
DELETE\s+FROM\s+\w+\s*(?:;|$)|DELETE without WHERE clause — deletes every row in the table
:wq!|Vim force-write — not dangerous per se but flagged in scripts
EOF
)

# Normalize command: collapse whitespace, lowercase for matching
NORMALIZED=$(echo "$COMMAND" | tr -s ' ')

BLOCKED=false
BLOCKED_REASON=""

while IFS='|' read -r pattern reason; do
    [ -z "$pattern" ] && continue
    if echo "$NORMALIZED" | grep -qiE "$pattern" 2>/dev/null; then
        BLOCKED=true
        BLOCKED_REASON="$reason"
        break
    fi
done <<< "$DANGEROUS_PATTERNS"

if [ "$BLOCKED" = true ]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    PROJECT_PATH=$(pwd)
    
    # Log the blocked attempt
    {
        echo "[$TIMESTAMP] BLOCKED | project=$PROJECT_PATH | command=$COMMAND | reason=$BLOCKED_REASON"
    } >> "$LOG_FILE"
    
    # Print user-friendly error to stderr (Claude displays this)
    cat >&2 << ERRMSG
    
╔══════════════════════════════════════════════════════════════╗
║  🛑 COMMAND BLOCKED BY SECURITY HOOK                        ║
╠══════════════════════════════════════════════════════════════╣
║  Command: $COMMAND
║  Reason:  $BLOCKED_REASON
║                                                             ║
║  If you need to run this command anyway:                    ║
║  1. Manually execute it in your terminal                    ║
║  2. Or temporarily disable this hook:                       ║
║     mv ~/.claude/hooks/block-dangerous.sh ~/.claude/hooks/  ║
║     block-dangerous.sh.disabled                             ║
╚══════════════════════════════════════════════════════════════╝
ERRMSG
    
    exit 2
fi

exit 0
