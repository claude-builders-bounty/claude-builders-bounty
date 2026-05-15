#!/usr/bin/env bash
# Pre-tool-use hook: blocks destructive bash commands
# Install: save to ~/.claude/hooks/pre-tool-use.sh and chmod +x

LOG_FILE="$HOME/.claude/hooks/blocked.log"
COMMAND="$1"

# Dangerous patterns to block
DANGEROUS_PATTERNS=(
  "rm -rf"
  "DROP TABLE"
  "git push --force"
  "TRUNCATE"
  "DELETE FROM"
  "rm -r /"
  "mkfs"
  "dd if=/dev/zero"
  "shutdown"
  "reboot"
  ":(){ :|:& };:"
)

is_blocked=0
blocked_pattern=""

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    is_blocked=1
    blocked_pattern="$pattern"
    break
  fi
done

# Special check for DELETE FROM without WHERE
if echo "$COMMAND" | grep -qiE "DELETE FROM" && ! echo "$COMMAND" | grep -qiE "WHERE"; then
  is_blocked=1
  blocked_pattern="DELETE FROM without WHERE clause"
fi

if [[ $is_blocked -eq 1 ]]; then
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  project_path="${PWD:-unknown}"
  
  echo "[$timestamp] BLOCKED: $COMMAND | Pattern: $blocked_pattern | Path: $project_path" >> "$LOG_FILE"
  
  echo "⛔ BLOCKED: This command matches a dangerous pattern: '$blocked_pattern'"
  echo ""
  echo "Reason: This command could cause irreversible data loss or security issues."
  echo ""
  echo "If you need to perform this action, please:"
  echo "  1. Verify the target is correct"
  echo "  2. Create a backup first"
  echo "  3. Ask for explicit confirmation before proceeding"
  echo ""
  echo "Log entry: $timestamp | $COMMAND | $blocked_pattern"
  exit 1
fi

exit 0
