#!/usr/bin/env bash
# Claude Code pre-tool-use hook: blocks dangerous commands
# Install: cp to ~/.claude/hooks/pre-tool-use-guard.sh && chmod +x ~/.claude/hooks/pre-tool-use-guard.sh

HOOK_INPUT=$(cat)
COMMAND=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "DROP TABLE"
  "TRUNCATE"
  "git push --force"
  "git push -f"
  "DELETE FROM"
  "mkfs"
  "dd if="
  "> /dev/sd"
  "chmod -R 777 /"
  ":(){ :|:& };:"
)

BLOCKED=false
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qi "$pattern"; then
    BLOCKED=true
    MATCHED="$pattern"
    break
  fi
done

if [ "$BLOCKED" = true ]; then
  TIMESTAMP=$(date -Iseconds)
  PROJECT=$(pwd)
  echo "[$TIMESTAMP] BLOCKED | Pattern: $MATCHED | Command: $COMMAND | Project: $PROJECT" >> "$LOG_FILE"
  echo "{\"decision\":\"block\",\"reason\":\"Dangerous command blocked: matched pattern '$MATCHED'. This command could cause irreversible damage. If you're sure, ask the user for explicit confirmation.\"}"
else
  echo "{\"decision\":\"allow\"}"
fi
