#!/bin/bash
set -e
LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE" 2>/dev/null || true
CMD_LINE=""
if [ ! -t 0 ]; then CMD_LINE=$(cat 2>/dev/null || echo ""); fi
FULL_CMD="${CMD_LINE:-$*}"
[ -z "$FULL_CMD" ] && exit 0
PATTERNS=("rm -rf[[:space:]]+/" "rm[[:space:]]+-rf[[:space:]]+--no-preserve-root" "DROP[[:space:]]+TABLE" "git[[:space:]]+push[[:space:]]+--force" "git[[:space:]]+push[[:space:]]+-f[[:space:]]" "TRUNCATE[[:space:]]+")
if echo "$FULL_CMD" | grep -qiE "^[[:space:]]*DELETE[[:space:]]+FROM"; then
  if ! echo "$FULL_CMD" | grep -qiE "[[:space:]]+WHERE[[:space:]]+"; then
    TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$TS] BLOCKED | project=${PWD:-unknown} | command=$FULL_CMD" >> "$LOG_FILE"
    echo "SECURITY BLOCK: DELETE FROM without WHERE clause. Logged: $LOG_FILE" >&2
    exit 1
  fi
fi
for pattern in "${PATTERNS[@]}"; do
  if echo "$FULL_CMD" | grep -qiE "$pattern"; then
    TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$TS] BLOCKED | project=${PWD:-unknown} | command=$FULL_CMD" >> "$LOG_FILE"
    echo "SECURITY BLOCK: Destructive command prevented. Logged: $LOG_FILE" >&2
    exit 1
  fi
done
exit 0
