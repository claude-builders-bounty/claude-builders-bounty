#!/usr/bin/env bash
# pre-tool-use.sh — Claude Code Pre-Tool-Use Hook
# Blocks destructive bash commands before execution.
# Install: cp this file ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
SCRIPT_NAME="$(basename "$0")"

# Dangerous patterns — each line: regex|reason
DANGEROUS_PATTERNS=$(cat <<'RULES'
rm -rf[[:space:]]+/[[:space:]]*$|Recursive root deletion (rm -rf /)
rm -rf[[:space:]]+/[[:space:]]*\*|Recursive root wildcard deletion (rm -rf /*)
rm -rf[[:space:]]+/home[[:space:]]*$|Home directory deletion (rm -rf /home)
rm[[:space:]]+-rf[[:space:]]+--no-preserve-root|Dangerous rm with no-preserve-root
dd[[:space:]]+if=|Disk destruction via dd
mkfs\.|Filesystem formatting
fdisk[[:space:]]+/dev|Partition table modification
parted[[:space:]]+/dev|Partition editing
>[[:space:]]*/dev/sd|Writing directly to block device
chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+/|Permission bombing root
:\(\)[[:space:]]*\{[[:space:]]*:[|:\(\)[[:space:]]*\{|Fork bomb detection
wget.*\|.*(bash|sh)|wget pipe to shell (dangerous)
curl.*\|.*(bash|sh)|curl pipe to shell (dangerous)
sudo[[:space:]]+rm[[:space:]]+-rf|Escalated recursive deletion
mv[[:space:]]+/[[:space:]]+/dev/null|Moving root to null
shutdown[[:space:]]+(now|-h|-r|0)|System shutdown in CI
reboot|System reboot
halt|System halt
DROP[[:space:]]+TABLE|SQL table deletion
TRUNCATE[[:space:]]+TABLE|SQL table truncation
DELETE[[:space:]]+FROM(?!.*WHERE)|SQL delete without WHERE clause
git[[:space:]]+push[[:space:]]+--force|Force push to git
git[[:space:]]+push[[:space:]]+-f|Force push to git (short form)
RULES
)

log_block() {
  local cmd="$1" reason="$2" ts
  ts="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "[${ts}] [BLOCKED] ${reason} | project=$(pwd) | cmd=${cmd:0:200}" >> "$LOG_FILE"
}

check_command() {
  local cmd="$1"
  local IFS=$'\n'
  for rule in $DANGEROUS_PATTERNS; do
    [ -z "$rule" ] && continue
    local pattern="${rule%%|*}"
    local reason="${rule#*|}"
    if echo "$cmd" | grep -qiE "$pattern" 2>/dev/null; then
      echo "[SECURITY] BLOCKED: ${reason}" >&2
      echo "[SECURITY] Command was: ${cmd:0:200}" >&2
      echo "[SECURITY] To disable this hook temporarily: rm ~/.claude/hooks/pre-tool-use" >&2
      log_block "$cmd" "$reason"
      exit 1
    fi
  done
  exit 0
}

# Parse stdin for Bash tool calls
if [ ! -t 0 ]; then
  while IFS= read -r line; do
    INPUT_JSON="$INPUT_JSON$line"
  done

  # Try to extract command from JSON structure
  CMD=$(echo "$INPUT_JSON" | grep -oP '"command"\s*:\s*"([^"]+)"' | head -1 | sed 's/"command"\s*:\s*"//' | sed 's/"$//' 2>/dev/null || true)

  if [ -n "$CMD" ]; then
    check_command "$CMD"
  fi
fi

# Also support direct command-line argument
if [ $# -ge 1 ]; then
  check_command "$*"
fi

exit 0
