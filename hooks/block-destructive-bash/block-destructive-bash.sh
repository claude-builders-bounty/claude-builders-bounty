#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands (Bash version)
# Solves Bounty #3 ($100) in claude-builders-bounty

set -euo pipefail

INPUT=$(cat)
[ -z "$INPUT" ] && exit 0

COMMAND=""
CWD="$(pwd)"

if echo "$INPUT" | grep -q '^{' ; then
    # Try parsing tool_input.command via python or grep
    COMMAND=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tool_input', {}).get('command', ''))" 2>/dev/null || true)
fi

if [ -z "$COMMAND" ]; then
    COMMAND="$INPUT"
fi

REASON=""

if echo "$COMMAND" | grep -Ei '\brm\s+.*(-(r.*f|f.*r)|--force.*--recursive|--recursive.*--force|-r\s+-f|-f\s+-r)' >/dev/null; then
    REASON="Recursive forced file removal (rm -rf)"
elif echo "$COMMAND" | grep -Ei '\bDROP\s+TABLE\b' >/dev/null; then
    REASON="Destructive SQL schema command (DROP TABLE)"
elif echo "$COMMAND" | grep -Ei '\bgit\s+push\b.*(\s+--force\b|\s+-f\b|\s+--force-with-lease\b)' >/dev/null; then
    REASON="Forced git push history overwrite (git push --force)"
elif echo "$COMMAND" | grep -Ei '\bTRUNCATE(\s+TABLE)?\s+[a-zA-Z0-9_`\"'\.]+\b' >/dev/null; then
    REASON="Destructive SQL table wipe (TRUNCATE)"
elif echo "$COMMAND" | grep -Ei '\bDELETE\s+FROM\s+[a-zA-Z0-9_`\"'\.]+(\s*;|\s*$)' >/dev/null && ! echo "$COMMAND" | grep -Ei '\bWHERE\b' >/dev/null; then
    REASON="Unconstrained SQL delete without WHERE clause"
fi

if [ -n "$REASON" ]; then
    LOG_DIR="$HOME/.claude/hooks"
    mkdir -p "$LOG_DIR"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$TIMESTAMP] BLOCKED: \"$COMMAND\" | CWD: $CWD | REASON: $REASON" >> "$LOG_DIR/blocked.log"

    cat << EOF >&2

🚨 [BLOCKED BY HOOK] Destructive bash command intercepted!
Command: $COMMAND
Detected Hazard: $REASON
Explanation: For safety, irreversible commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, and DELETE without WHERE) are blocked automatically.
EOF
    exit 1
fi

exit 0
