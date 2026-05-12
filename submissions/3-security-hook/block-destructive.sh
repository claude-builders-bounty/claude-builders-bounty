#!/usr/bin/env bash
# Claude Code pre-tool-use hook — blocks destructive commands
# Install: mkdir -p ~/.claude/hooks/pre-tool-use
#          ln -sf "$PWD/block-destructive.sh" ~/.claude/hooks/pre-tool-use/
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
LOG_FILE="$HOOK_DIR/pre-tool-use/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

DANGEROUS_PATTERNS=(
  "rm[[:space:]]+-[rR][fF][[:space:]]+"
  "rm[[:space:]]+-[fF][rR][[:space:]]+"
  "rm[[:space:]]+-rf[[:space:]]+--no-preserve-root"
  "DROP[[:space:]]+TABLE"
  "DROP[[:space:]]+DATABASE"
  "TRUNCATE[[:space:]]+"
  "DELETE[[:space:]]+FROM[[:space:]]+[^W]"
  "git[[:space:]]+push[[:space:]]+--force"
  "git[[:space:]]+push[[:space:]]+-[fF]"
  "mkfs\."
  ":\(\)[[:space:]]*\{[[:space:]]*:[|:]"
  "chmod[[:space:]]+-R[[:space:]]+0+[[:space:]]+/"
  "chown[[:space:]]+-R[[:space:]]+/"
)

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | head -c 500)
BLOCKED=false
MATCHED=""

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    BLOCKED=true
    MATCHED="$pattern"
    break
  fi
done

if [ "$BLOCKED" = true ]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT="${PWD}"
  
  echo "[$TIMESTAMP] BLOCKED | cmd: $COMMAND | project: $PROJECT" >> "$LOG_FILE"
  
  echo '{"allowed":false,"reason":"Blocked by security hook","message":"⛔ Destructive command blocked. Check ~/.claude/hooks/pre-tool-use/blocked.log for details."}'
  exit 0
fi

echo "$INPUT"
