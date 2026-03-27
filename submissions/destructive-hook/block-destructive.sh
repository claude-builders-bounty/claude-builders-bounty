#!/bin/bash
set -e

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

if [ -z "$COMMAND" ]; then
  exit 0
fi

BLOCKED_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf \."
  "DROP TABLE"
  "DROP DATABASE"
  "TRUNCATE "
  "git push --force"
  "git push -f "
  "git reset --hard"
  "DELETE FROM.*WHERE 1"
  "DELETE FROM.*WITHOUT"
  "> /dev/sda"
  "mkfs\."
  "dd if=/dev/zero"
  "chmod -R 777 /"
  ":(){ :|:& };:"
)

PROJECT_PATH=$(pwd)
LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$TIMESTAMP] BLOCKED: '$COMMAND' in $PROJECT_PATH" >> "$LOG_FILE"
    
    echo "{\"decision\": \"block\", \"reason\": \"Destructive command blocked: matches pattern '$pattern'. Command: $COMMAND\"}"
    exit 0
  fi
done

# Check DELETE FROM without WHERE clause
if echo "$COMMAND" | grep -qiE "DELETE FROM" && ! echo "$COMMAND" | grep -qiE "WHERE"; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "[$TIMESTAMP] BLOCKED: '$COMMAND' (DELETE without WHERE) in $PROJECT_PATH" >> "$LOG_FILE"
  echo "{\"decision\": \"block\", \"reason\": \"DELETE FROM without WHERE clause detected. This would delete all rows.\"}"
  exit 0
fi

exit 0
