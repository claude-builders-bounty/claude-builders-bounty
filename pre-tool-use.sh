#!/bin/bash
# Claude Code pre-tool-use hook - blocks destructive commands
BLOCKED_LOG="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$BLOCKED_LOG")"
PATTERNS=("rm -rf /" "rm -rf ~" "DROP TABLE" "DROP DATABASE" "git push --force" "git push -f" ":(){ :|:& };" "chmod -R 000" "mkfs\." "eval \$")
INPUT=$(cat)
for pattern in "${PATTERNS[@]}"; do
  if echo "$INPUT" | grep -qiE "$pattern"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED: $pattern" >> "$BLOCKED_LOG"
    echo "BLOCKED by security hook: command matches pattern [$pattern]"
    echo "Logged to: $BLOCKED_LOG"
    exit 1
  fi
done
echo "$INPUT"
