#!/usr/bin/env bash
# pre-tool-use hook — blocks destructive bash commands
# Place in ~/.claude/hooks/pre-tool-use.sh
# Claude Code runs this before executing bash commands.

LOG_FILE="$HOME/.claude/hooks/blocked.log"
# Read the command from Claude's pre-tool-use stdin or argument
COMMAND="${CLAUDE_TOOL_ARGS:-$*}"

# Dangerous patterns to block
DANGEROUS_PATTERNS=(
  "rm[[:space:]]+-rf"
  "DROP[[:space:]]+TABLE"
  "git[[:space:]]+push[[:space:]]+--force"
  "TRUNCATE[[:space:]]+TABLE"
  "DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_]+[[:space:]]*;?$"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    PROJECT_PATH=$(pwd)
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$TIMESTAMP] BLOCKED: $COMMAND | project: $PROJECT_PATH" >> "$LOG_FILE"
    cat << 'EOF'
🚫 BLOCKED: Destructive command detected

Type: Pattern matched
This command was intercepted by the safety hook.
If you intentionally need to run this, use:
  git push --force-with-lease  (instead of --force)
  Use application-level safe deletion instead of rm -rf
  Use database migrations for schema changes

Logged to: ~/.claude/hooks/blocked.log
EOF
    exit 1
  fi
done

exit 0
