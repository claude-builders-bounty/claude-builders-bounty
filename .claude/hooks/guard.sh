#!/bin/bash
# guard.sh - Pre-tool-use hook that blocks destructive bash commands
#
# Receives JSON on stdin: { "tool_name": "Bash", "tool_input": { "command": "..." } }
# Returns JSON on stdout to deny, or exits 0 to allow.
#
# Configuration: edit BLOCKLIST and ALLOWLIST below.
# Logs are written to ~/.claude/hooks/blocked.log

set -e

# ── Configuration ──────────────────────────────────────────────────────────────
# Log file for blocked commands
LOG_FILE="${HOME}/.claude/hooks/blocked.log"

# Patterns that trigger a block (extended regex). Add or remove as needed.
BLOCKLIST=(
  'rm[[:space:]]+(-[^ ]*)?[[:space:]]*(-rf|r[[:space:]]*-f|-f[[:space:]]*r)[[:space:]]+/'
  'rm[[:space:]]+(-[^ ]*)?[[:space:]]*(-rf|r[[:space:]]*-f|-f[[:space:]]*r)[[:space:]]+--no-preserve-root'
  'dd[[:space:]]+if='
  ':\(\)[[:space:]]*\{[[:space:]]*:[|&]'
  'mkfs\.'
  'mkfs[[:space:]]'
  'parted[[:space:]]+/dev/[a-z]+[[:space:]]+mklabel'
  'fdisk[[:space:]]+/dev/[a-z]+'
  'format[[:space:]]+[a-z]:'
  'chmod[[:space:]]+-R[[:space:]]*777'
  'chmod[[:space:]]+777[[:space:]]+/'
  'chown[[:space:]]+-R[[:space:]]+[^ ]+[[:space:]]+/'
  'sudo[[:space:]]+rm[[:space:]]+(-[^ ]*)?[[:space:]]*(-rf|r[[:space:]]*-f|-f[[:space:]]*r)?'
  'sudo[[:space:]]+shutdown'
  'sudo[[:space:]]+reboot'
  'sudo[[:space:]]+halt'
  'sudo[[:space:]]+poweroff'
  'sudo[[:space:]]+init[[:space:]]+0'
  'sudo[[:space:]]+init[[:space:]]+6'
  'wget[[:space:]]+.*\|[[:space:]]*bash'
  'wget[[:space:]]+.*\|[[:space:]]*sh[[:space:]]'
  'curl[[:space:]]+.*\|[[:space:]]*bash'
  'curl[[:space:]]+.*\|[[:space:]]*sh[[:space:]]'
  'DROP[[:space:]]+TABLE'
  'DROP[[:space:]]+DATABASE'
  'TRUNCATE[[:space:]]+TABLE'
  'DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*;?[[:space:]]*$'
  'git[[:space:]]+push[[:space:]]+--force'
  'git[[:space:]]+push[[:space:]]+-f[[:space:]]'
  '>[[:space:]]*/dev/sd[a-z]'
  '>[[:space:]]*/dev/nvme[0-9]'
  '>[[:space:]]*/dev/mmcblk[0-9]'
  'pv[[:space:]]+</dev/sd'
  'cat[[:space:]]+/dev/zero[[:space:]]+>/dev/sd'
  'shutdown[[:space:]]+-(h|r|now|t[[:space:]]+0)'
  'reboot[[:space:]]+--force'
  'init[[:space:]]+0'
  'init[[:space:]]+6'
  'telinit[[:space:]]+0'
  'telinit[[:space:]]+6'
)

# Patterns that are always allowed (overrides blocklist)
ALLOWLIST=(
  'rm[[:space:]]+(-[^ ]*)?[[:space:]]*(-rf|r[[:space:]]*-f|-f[[:space:]]*r)[[:space:]]+/tmp/'
  'rm[[:space:]]+(-[^ ]*)?[[:space:]]*(-rf|r[[:space:]]*-f|-f[[:space:]]*r)[[:space:]]+\./(node_modules|dist|build|target|.next|out)'
  'rm[[:space:]]+(-[^ ]*)?[[:space:]]*(-rf|r[[:space:]]*-f|-f[[:space:]]*r)[[:space:]]+"?\.\/?'
  'wget[[:space:]]+.*install'
  'curl[[:space:]]+.*install'
)

# ── Functions ──────────────────────────────────────────────────────────────────

log_blocked() {
  local cmd="$1"
  local pattern="$2"
  local project_path="${3:-unknown}"
  local timestamp
  timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

  mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
  printf '[%s] BLOCKED pattern="%s" cmd="%s" project="%s"\n' \
    "$timestamp" "$pattern" "$cmd" "$project_path" >> "$LOG_FILE" 2>/dev/null || true
}

deny_command() {
  local cmd="$1"
  local reason="$2"
  local pattern="$3"
  local project_path="${4:-unknown}"

  log_blocked "$cmd" "$pattern" "$project_path"

  jq -n --arg reason "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
}

allow_command() {
  exit 0
}

# ── Main ───────────────────────────────────────────────────────────────────────

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool name and command
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-unknown}"

# Only evaluate Bash tool calls
if [ "$TOOL_NAME" != "Bash" ] || [ -z "$COMMAND" ]; then
  allow_command
fi

# First check allowlist (overrides blocklist)
for pattern in "${ALLOWLIST[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    allow_command
  fi
done

# Check blocklist
for pattern in "${BLOCKLIST[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    deny_command "$COMMAND" \
      "Blocked by guard.sh: command matches dangerous pattern '${pattern}'. This operation is not permitted for security reasons." \
      "$pattern" \
      "$PROJECT_DIR"
    exit 0
  fi
done

# Allow all other commands
allow_command
