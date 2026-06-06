#!/usr/bin/env bash
# ============================================================
# block-destructive.sh — Pre-tool-use hook for Claude Code
#
# Blocks dangerous bash commands before execution.
# Bounty: claude-builders-bounty #3 ($100)
#
# Install: See README.md or settings-snippet.json
# ============================================================
set -euo pipefail

# --- config -------------------------------------------------
LOG_FILE="${HOME}/.claude/hooks/blocked.log"
DRY_RUN=false  # Set to "true" to only warn, not block

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# --- read hook input from stdin -----------------------------
HOOK_INPUT=$(cat)

# Only process Bash tool calls
TOOL_NAME=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || \
            echo "$HOOK_INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)

if [[ "$TOOL_NAME" != "Bash" ]]; then
  # Not a bash command — allow
  echo '{"continue": true}'
  exit 0
fi

# Extract the command
COMMAND=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || \
          echo "$HOOK_INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || true)

if [[ -z "$COMMAND" ]]; then
  echo '{"continue": true}'
  exit 0
fi

# Normalize for matching: lowercase, collapse whitespace
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]' | tr -s ' ')

# --- dangerous patterns -------------------------------------
# Format: "regex|||reason"
# Separator is triple-pipe to avoid conflict with regex alternation |
PATTERNS=(
  # Filesystem destruction
  "rm\s+-rf\s+/|||FILESYSTEM_DESTROY: recursive force remove from root"
  "rm\s+-rf\s+\*\s*/|||FILESYSTEM_DESTROY: recursive force remove with glob to root"
  "rm\s+-rf\s+~|||FILESYSTEM_DESTROY: remove home directory"
  "rm\s+-rf\s+\$HOME|||FILESYSTEM_DESTROY: remove HOME variable path"
  "rm\s+-rf\s+/boot|||FILESYSTEM_DESTROY: remove boot partition"
  "rm\s+-rf\s+/etc|||FILESYSTEM_DESTROY: remove /etc configuration"
  "rm\s+-rf\s+/usr|||FILESYSTEM_DESTROY: remove /usr binaries"
  "rm\s+-rf\s+/var|||FILESYSTEM_DESTROY: remove /var data"
  ">\s*/dev/sd[a-z]|||FILESYSTEM_DESTROY: overwrite raw block device"
  "dd\s+if=.*of=/dev/sd|||FILESYSTEM_DESTROY: dd to raw block device"
  "mkfs\.|||FILESYSTEM_DESTROY: format filesystem"

  # Database destruction
  "drop\s+table|||DB_DESTROY: DROP TABLE statement"
  "drop\s+database|||DB_DESTROY: DROP DATABASE statement"
  "truncate\s+(table\s+)?\w|||DB_DESTROY: TRUNCATE TABLE statement"
  "delete\s+from\s+\w+\s*[^w]|||DB_DESTROY: DELETE FROM without WHERE clause"
  "delete\s+from\s+\w+\s*$|||DB_DESTROY: DELETE FROM without WHERE clause"

  # Git force push
  "git\s+push\s+(-f|--force)|||GIT_FORCE: force push to remote"
  "git\s+push\s+.*--delete|||GIT_FORCE: delete remote branch"
  "git\s+push\s+.*:\s*$|||GIT_FORCE: delete remote branch (short syntax)"
  "git\s+reset\s+--hard|||GIT_DESTRUCTIVE: hard reset (loses uncommitted work)"
  "git\s+clean\s+-[a-z]*f|||GIT_DESTRUCTIVE: git clean with force flag"

  # Fork bomb & resource exhaustion
  ":\s*\(\s*\)\s*{\s*:\s*|\s*:\s*&\s*}|||FORK_BOMB: shell fork bomb pattern"
  ":\(\)\s*{\s*:\s*|:\s*&\s*}|||FORK_BOMB: shell fork bomb pattern"

  # System commands that destroy state
  "shutdown\s+-h\s+now|||SYSTEM: immediate system shutdown"
  "shutdown\s+-r\s+now|||SYSTEM: immediate system reboot"
  "reboot|||SYSTEM: system reboot"
  "chmod\s+-R\s+777\s+/|||PERMISSION: recursive 777 on root"
  "chown\s+-R\s+\w+:\w+\s+/|||PERMISSION: recursive chown on root"
)

# --- check each pattern -------------------------------------
BLOCKED_REASON=""
for entry in "${PATTERNS[@]}"; do
  PATTERN="${entry%%|||*}"
  REASON="${entry##*|||}"

  if echo "$CMD_LOWER" | grep -qE "$PATTERN" 2>/dev/null; then
    BLOCKED_REASON="$REASON"
    break
  fi
done

if [[ -n "$BLOCKED_REASON" ]]; then
  # --- log the attempt --------------------------------------
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  cat >> "$LOG_FILE" <<LOGENTRY
[$TIMESTAMP] BLOCKED — $BLOCKED_REASON
  Command: $COMMAND
  Hook input: $HOOK_INPUT
---
LOGENTRY

  if $DRY_RUN; then
    # Warn but allow
    cat >&2 <<WARN
╔══════════════════════════════════════════════════════════════╗
║ ⚠️  DANGEROUS COMMAND DETECTED (dry-run: allowing anyway)    ║
║   Reason: $BLOCKED_REASON
║   Command: $COMMAND
╚══════════════════════════════════════════════════════════════╝
WARN
    echo '{"continue": true}'
  else
    # Block
    cat >&2 <<BLOCK
╔══════════════════════════════════════════════════════════════╗
║ ⛔ DANGEROUS COMMAND BLOCKED                                  ║
║   Reason: $BLOCKED_REASON
║   Command: $COMMAND
║   Logged: $LOG_FILE
╚══════════════════════════════════════════════════════════════╝
BLOCK
    # Return blocking decision
    printf '{"continue":false,"stopReason":"Dangerous command blocked: %s"}' "$BLOCKED_REASON"
  fi
else
  # Safe — allow
  echo '{"continue": true}'
fi
