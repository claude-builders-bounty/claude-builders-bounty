#!/usr/bin/env bash
#
# pre-tool-use hook — blocks destructive bash commands
#
# Claude Code calls this hook before each tool execution.
# It receives the tool call JSON (or relevant pieces) on stdin.
# Exit 0 = allow, exit non-zero = block.
#
# Installation: ln -sf "$PWD" ~/.claude/hooks/pre-tool-use
#
set -o pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="${PWD}"

# ---- Read the JSON payload from stdin ----
# Claude Code passes something like: {"tool":"Bash","command":"rm -rf /"}
# We extract the 'command' field (or "input" / "value" depending on version).
# For safety, scan the whole JSON string.

INPUT_JSON=""
if [ ! -t 0 ]; then
  INPUT_JSON=$(cat)
fi

# If empty, allow through
if [ -z "$INPUT_JSON" ]; then
  exit 0
fi

# ---- Blocked patterns (case-insensitive) ----
BLOCKED_PATTERNS=(
  'rm[[:space:]]+-rf[[:space:]]+[\/]'
  'rm[[:space:]]+-rf[[:space:]]+\~'
  'rm[[:space:]]+-rf[[:space:]]+/[[:space:]]*\*'
  'DROP[[:space:]]+TABLE'
  'TRUNCATE[[:space:]]+'
  'DELETE[[:space:]]+FROM[[:space:]]+[^[:space:]]+[[:space:]]*(;[[:space:]]*$|$)'
  'git[[:space:]]+push[[:space:]]+--force'
  'git[[:space:]]+push[[:space:]]+-f'
  'git[[:space:]]+push[[:space:]]+--force-with-lease'
  'curl[[:space:]]+.*\|[[:space:]]*bash'
  'wget[[:space:]]+.*\|[[:space:]]*bash'
  'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+/'
  'dd[[:space:]]+if=/dev/zero'
  'mkfs\.'
  'mkswap'
  '>\s+/dev/sda'
)

# ---- Check if the command is dangerous ----
ATTEMPTED_CMD="$INPUT_JSON"
for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$ATTEMPTED_CMD" | grep -qiE "$pattern"; then
    TIMESTAMP="$(date '+%Y-%m-%dT%H:%M:%S%z')"

    # Log the blocked attempt
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[${TIMESTAMP}] BLOCKED: pattern='${pattern}' cmd='${ATTEMPTED_CMD}' project='${PROJECT_PATH}'" >> "$LOG_FILE"

    # Tell Claude why — print to stderr so it shows up
    echo "⚠️  BLOCKED: Dangerous command detected (matched pattern: ${pattern})" >&2
    echo "   This command was intercepted by the pre-tool-use security hook." >&2
    echo "   Blocked attempt logged to: ${LOG_FILE}" >&2
    echo "   If you need to run this command, use the web UI or terminal directly." >&2

    exit 1
  fi
done

# ---- Not blocked — allow ----
exit 0
