#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands (Bash implementation)
# Fulfills Bounty #3 on claude-builders-bounty

set -eo pipefail

COMMAND="$*"
if [ -z "$COMMAND" ]; then
  if [ ! -t 0 ]; then
    COMMAND=$(cat)
  fi
fi

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Extract command from JSON if wrapped
if [[ "$COMMAND" =~ \"command\":[[:space:]]*\"([^\"]+)\" ]]; then
  COMMAND="${BASH_REMATCH[1]}"
fi

LOG_FILE="${CLAUDE_HOOK_LOG_PATH:-$HOME/.claude/hooks/blocked.log}"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

block_and_exit() {
  local REASON="$1"
  local TIMESTAMP
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date)
  echo "[$TIMESTAMP] REASON: $REASON | CWD: $(pwd) | CMD: $COMMAND" >> "$LOG_FILE"

  >&2 echo ""
  >&2 echo "🚨 [CLAUDE CODE SECURITY GUARD: COMMAND BLOCKED]"
  >&2 echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  >&2 echo "Reason:  Destructive command prohibited: $REASON"
  >&2 echo "Command: $COMMAND"
  >&2 echo "Path:    $(pwd)"
  >&2 echo "Logged:  $LOG_FILE"
  >&2 echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  >&2 echo "Action: Command was intercepted and stopped before execution."
  >&2 echo ""
  exit 1
}

# 1. rm -rf
if [[ "$COMMAND" =~ rm[[:space:]]+.*-[a-zA-Z]*r[a-zA-Z]*f ]] || [[ "$COMMAND" =~ rm[[:space:]]+.*-[a-zA-Z]*f[a-zA-Z]*r ]] || [[ "$COMMAND" =~ rm[[:space:]]+.*--recursive.*--force ]] || [[ "$COMMAND" =~ rm[[:space:]]+.*--force.*--recursive ]]; then
  block_and_exit "rm -rf (Recursive forced directory removal)"
fi

# 2. DROP TABLE
if echo "$COMMAND" | grep -Ei '\bdrop[[:space:]]+table\b' >/dev/null 2>&1; then
  block_and_exit "DROP TABLE (Database table destruction)"
fi

# 3. git push --force
if echo "$COMMAND" | grep -Ei '\bgit[[:space:]]+push\b.*(--force|-f\b|--force-with-lease\b)' >/dev/null 2>&1; then
  block_and_exit "git push --force (Remote git history overwrite)"
fi

# 4. TRUNCATE
if echo "$COMMAND" | grep -Ei '\btruncate[[:space:]]+(table[[:space:]]+)?[a-zA-Z0-9_]+' >/dev/null 2>&1; then
  block_and_exit "TRUNCATE (Table data wipe)"
fi

# 5. DELETE FROM without WHERE
if echo "$COMMAND" | grep -Ei '\bdelete[[:space:]]+from[[:space:]]+[a-zA-Z0-9_`"'\''"]+([[:space:]]*;?[[:space:]]*$)' >/dev/null 2>&1; then
  block_and_exit "DELETE FROM without WHERE clause (Unconditional table purge)"
fi

exit 0
