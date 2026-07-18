#!/bin/bash
set -euo pipefail
COMMAND="${1:-}"
LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

is_destructive() {
    local cmd="$1"
    echo "$cmd" | grep -qiE '(^|\||;)rm\s+(-rf?|--recursive|--force)' && return 0
    echo "$cmd" | grep -qiE '(^|\||;)DROP\s+TABLE' && return 0
    echo "$cmd" | grep -qiE '(^|\||;)git\s+push\s+(--force|-f)\s' && return 0
    echo "$cmd" | grep -qiE '(^|\||;)TRUNCATE\s' && return 0
    echo "$cmd" | grep -qiE '(^|\||;)DELETE\s+FROM\s+\w+\s+(WHERE\s+1=1|$)' && return 0
    echo "$cmd" | grep -qiE '(^|\||;)chmod\s+777' && return 0
    echo "$cmd" | grep -qiE '(^|\||;)>(>)?\s*/dev/' && return 0
    return 1
}
if is_destructive "$COMMAND"; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[BLOCKED] $TIMESTAMP | CMD: $COMMAND" >> "$LOG_FILE"
    echo "ERROR: Destructive command blocked. Logged to: $LOG_FILE"
    exit 1
fi
exit 0
