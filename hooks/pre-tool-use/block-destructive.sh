#!/usr/bin/env bash
# pre-tool-use hook: blocks destructive bash commands
# Install: ln -sf "$PWD/block-destructive.sh" ~/.claude/hooks/pre-tool-use/block-destructive.sh

BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"

# Read the command from stdin or env
COMMAND="${CLAUDE_TOOL_INPUT:-$(cat)}"

# Dangerous patterns
PATTERNS=(
  "rm[[:space:]]+-rf"
  "DROP[[:space:]]+TABLE"
  "git[[:space:]]+push[[:space:]]+--force"
  "TRUNCATE[[:space:]]+"
  "DELETE[[:space:]]+FROM[[:space:]]+[^[:space:]]+[[:space:]]*$"
)

for pattern in "${PATTERNS[@]}"; do
  if [[ "$COMMAND" =~ $pattern ]]; then
    TIMESTAMP=$(date --iso-8601=seconds)
    PROJECT_PATH="${PWD}"
    echo "[${TIMESTAMP}] BLOCKED | project=${PROJECT_PATH} | pattern=${pattern} | command=${COMMAND}" >> "$BLOCKED_LOG"
    echo "BLOCKED: Command matches dangerous pattern '${pattern}'. This command was intercepted by the pre-tool-use hook for your safety."
    echo "Logging to ${BLOCKED_LOG}"
    exit 1
  fi
done

exit 0
