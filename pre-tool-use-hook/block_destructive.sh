#!/bin/bash
# pre-tool-use hook for Claude Code
# Blocks destructive bash commands before execution
# Install: ln -sf "$(pwd)/block_destructive.sh" ~/.claude/hooks/pre-tool-use

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read the command from stdin
CMD=$(cat)

# Dangerous patterns — block immediately
DANGEROUS_PATTERNS=(
  'rm[[:space:]]+-rf'
  'rm[[:space:]]+-fr'
  'rm[[:space:]]+--recursive'
  'DROP[[:space:]]+TABLE'
  'DROP[[:space:]]+DATABASE'
  'TRUNCATE[[:space:]]+TABLE'
  "DELETE[[:space:]]+FROM[[:space:]]+[^[:space:]]+[[:space:]]*$"
  'git[[:space:]]+push[[:space:]]+--force'
  'git[[:space:]]+push[[:space:]]+-f[[:space:]]'
  'git[[:space:]]+commit[[:space:]]+--amend[[:space:]]+--no-edit'
  '>[[:space:]]*/dev/[hs]d'
  'mkfs\.'
  'dd[[:space:]]+if='
  ':(){[[:space:]]*:|:[[:space:]]*&};:'
  'chmod[[:space:]]+-R[[:space:]]+000[[:space:]]+/'
  'chown[[:space:]]+-R[[:space:]]+[^[:space:]]+[[:space:]]+/'
  'wget[[:space:]]+.*[|].*sh'
  'curl[[:space:]]+.*[|].*sh'
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qiE "$pattern"; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    PROJECT=$(pwd)
    echo "[$TIMESTAMP] BLOCKED | $PROJECT | $CMD" >> "$LOG_FILE"
    echo "❌ BLOCKED: This command was prevented by the pre-tool-use hook."
    echo "   Pattern matched: /$pattern/i"
    echo "   Logged to: $LOG_FILE"
    echo "   Reason: Potentially destructive operation."
    exit 1
  fi
done

exit 0
