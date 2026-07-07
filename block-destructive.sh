#!/bin/bash
# pre-tool-use hook: blocks destructive bash commands
# Install: ln -sf "$PWD/block-destructive.sh" ~/.claude/hooks/pre-tool-use

set -euo pipefail

BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="${PWD}"

# Read the command from stdin (Claude Code passes it via stdin)
INPUT=$(cat)

# Dangerous patterns to block
PATTERNS=(
  "rm -rf"
  "rm -rf /"
  "rm -fr"
  "DROP TABLE"
  "DROP DATABASE"
  "TRUNCATE TABLE"
  "git push --force"
  "git push -f"
  "DELETE FROM [a-zA-Z]+\s*(WHERE\s|$)"
)

for pattern in "${PATTERNS[@]}"; do
  if echo "$INPUT" | grep -qiE "$pattern"; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] BLOCKED | project=$PROJECT_PATH | pattern=$pattern | cmd=$INPUT" >> "$BLOCKED_LOG"
    cat <<EOF
⛔ BLOCKED: Destructive command detected

Claude attempted to run a command matching the blocked pattern: $pattern

Blocked at: $TIMESTAMP
Project: $PROJECT_PATH

This command was blocked by the pre-tool-use hook to prevent accidental data loss.
If you genuinely need to run this command, use the project's safety procedures
or run it manually after confirming the impact.

Logged to: $BLOCKED_LOG
EOF
    exit 1
  fi
done

# If no pattern matched, pass through
echo "$INPUT"
exit 0
