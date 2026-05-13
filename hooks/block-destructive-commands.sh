#!/usr/bin/env bash
# Claude Code PreToolUse hook: blocks destructive bash commands.
# Install: see README.md
set -euo pipefail

LOG_FILE="${CLAUDE_HOOKS_LOG:-$HOME/.claude/hooks/blocked.log}"
ALLOWLIST_FILE="${CLAUDE_HOOKS_ALLOWLIST:-$HOME/.claude/hooks/allowlist.txt}"

# Read JSON from stdin
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
if [[ "$TOOL_NAME" != "Bash" ]]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // "unknown"')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# --- Pattern definitions ---

# Destructive filesystem commands
FS_PATTERNS=(
  'rm\s+(-[a-zA-Z]*[rf]\s+.*?/|-\s*/)'
  'rm\s+-[a-zA-Z]*[rRfF][a-zA-Z]*\s+/'
  ':\(\)\{.*\|.*:&\s*\}:'            # fork bomb
  'mkfs\.'
  'dd\s+.*of=/dev/'
  'chmod\s+(-[a-zA-Z]*\s+)*777\s+/'
  '>\s*/dev/sd'
  'mv\s+/\*'
  'shred\s+'
  'wipefs\s+'
  'fdisk\s+/'
  'parted\s+.*rm\s'
)

# Remote code execution
RCE_PATTERNS=(
  'curl.*\|\s*(bash|sh|python|perl|ruby|node)'
  'wget.*\|\s*(bash|sh|python|perl|ruby|node)'
  'eval\s*\('
  'python.*-c.*import\s+os.*system'
)

# SQL destructive operations
SQL_PATTERNS=(
  'DROP\s+(TABLE|DATABASE|SCHEMA)\s'
  'TRUNCATE\s+(TABLE\s+)?'
  'DELETE\s+FROM\s+\S+\s*$'           # DELETE without WHERE
  'ALTER\s+TABLE\s+.*\s+DROP\s'
)

# Git destructive operations
GIT_PATTERNS=(
  'git\s+push\s+.*--force'
  'git\s+push\s+.*-f\b'
  'git\s+reset\s+--hard'
  'git\s+clean\s+-[a-zA-Z]*f'
  'git\s+branch\s+-[a-zA-Z]*D'
)

# System commands
SYS_PATTERNS=(
  'sudo\s+rm\s+-rf\s+/'
  'shutdown\s'
  'reboot\s'
  'halt\s'
  'poweroff\s'
  'init\s+0'
  'killall\s'
  'pkill\s+-9'
  'systemctl\s+(stop|disable)\s'
)

# --- Check functions ---

check_patterns() {
  local category="$1"
  shift
  local patterns=("$@")
  for pattern in "${patterns[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
      BLOCK_REASON="[$category] Blocked dangerous command matching pattern: $pattern"
      return 0
    fi
  done
  return 1
}

# --- Allowlist check ---
# If the command matches any line in the allowlist, skip all pattern checks
if [[ -f "$ALLOWLIST_FILE" ]]; then
  while IFS= read -r allowed; do
    [[ -z "$allowed" || "$allowed" == \#* ]] && continue
    if echo "$COMMAND" | grep -qF "$allowed"; then
      exit 0
    fi
  done < "$ALLOWLIST_FILE"
fi

# --- Main logic ---

BLOCK_REASON=""

if check_patterns "FILESYSTEM" "${FS_PATTERNS[@]}"; then
  :
elif check_patterns "REMOTE_CODE_EXEC" "${RCE_PATTERNS[@]}"; then
  :
elif check_patterns "SQL" "${SQL_PATTERNS[@]}"; then
  :
elif check_patterns "GIT" "${GIT_PATTERNS[@]}"; then
  :
elif check_patterns "SYSTEM" "${SYS_PATTERNS[@]}"; then
  :
fi

if [[ -n "$BLOCK_REASON" ]]; then
  # Log the blocked attempt
  mkdir -p "$(dirname "$LOG_FILE")"
  cat >> "$LOG_FILE" <<EOF
${TIMESTAMP} | session=${SESSION_ID} | cwd=${CWD} | command=${COMMAND} | reason=${BLOCK_REASON}
EOF

  # Output block decision
  jq -n \
    --arg reason "$BLOCK_REASON" \
    --arg cmd "$COMMAND" \
    '{
      "decision": "block",
      "reason": ("⚠️ " + $reason + "\n\nBlocked command: " + $cmd + "\n\nThis command was blocked by the destructive-command-guard hook to prevent potential data loss or system damage.\nIf you believe this is a false positive, you can temporarily disable the hook in .claude/settings.json.")
    }'
  exit 0
fi

# Allow the command
exit 0
