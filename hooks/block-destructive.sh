#!/usr/bin/env bash
# block-destructive.sh — Claude Code PreToolUse hook
# Blocks dangerous bash commands before they execute.
#
# Install:
#   mkdir -p ~/.claude/hooks
#   cp block-destructive.sh ~/.claude/hooks/
#   chmod +x ~/.claude/hooks/block-destructive.sh
#
# Add to your Claude Code settings (~/.claude/settings.json):
#   {
#     "hooks": {
#       "PreToolUse": [{
#         "matcher": "Bash",
#         "hooks": [{
#           "type": "command",
#           "command": "~/.claude/hooks/block-destructive.sh"
#         }]
#       }]
#     }
#   }

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
COMMAND=$(jq -r '.tool_input.command // empty' 2>/dev/null)
PROJECT_DIR=$(jq -r '.cwd // "unknown"' 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# ── Dangerous patterns ──────────────────────────────────────────────
# Each check returns a reason string if matched, empty otherwise.
check_dangerous() {
  local cmd="$1"

  # rm -rf (any variant)
  if echo "$cmd" | grep -qEi 'rm\s+.*-[[:alpha:]]*r[[:alpha:]]*-?[[:alpha:]]*f[[:alpha:]]*\s|rm\s+.*-[[:alpha:]]*f[[:alpha:]]*-?[[:alpha:]]*r[[:alpha:]]*\s|rm\s+--recursive\s+--force|rm\s+--force\s+--recursive'; then
    echo "rm -rf: recursive forced deletion detected"
    return
  fi

  # DROP TABLE
  if echo "$cmd" | grep -qEi 'DROP\s+TABLE'; then
    echo "DROP TABLE: destructive SQL detected"
    return
  fi

  # TRUNCATE
  if echo "$cmd" | grep -qEi 'TRUNCATE\s+TABLE|TRUNCATE\s+'; then
    echo "TRUNCATE: destructive SQL detected"
    return
  fi

  # git push --force (but allow --force-with-lease as intentional)
  if echo "$cmd" | grep -qEi 'git\s+push\s+.*--force(\s|$)'; then
    if ! echo "$cmd" | grep -q -- '--force-with-lease'; then
      echo "git push --force: force-push without --force-with-lease detected"
      return
    fi
  fi

  # DELETE FROM ... without WHERE clause
  if echo "$cmd" | grep -qEi 'DELETE\s+FROM' && ! echo "$cmd" | grep -qEi '\bWHERE\b'; then
    echo "DELETE FROM without WHERE: would delete all rows"
    return
  fi

  echo ""
}

REASON=$(check_dangerous "$COMMAND")

if [[ -n "$REASON" ]]; then
  # Log the blocked attempt
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "{\"timestamp\":\"${TIMESTAMP}\",\"command\":$(echo -n "$COMMAND" | jq -Rs .),\"project\":\"${PROJECT_DIR}\",\"reason\":\"${REASON}\"}" >> "$LOG_FILE"

  # Block the command
  jq -n --arg reason "$REASON" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: ("BLOCKED by safety hook: " + $reason + ". This command could cause irreversible damage. If you really need to run this, disable the hook temporarily.")
    }
  }'
  exit 0
fi

# Command is safe — allow it
exit 0
