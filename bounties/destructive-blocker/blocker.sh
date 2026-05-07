#!/bin/bash
# ============================================================================
# Claude Code Pre-Tool-Use Hook — Dangerous Command Blocker
# ============================================================================
# Blocks dangerous bash commands (rm -rf, DROP TABLE, git push --force,
# TRUNCATE, DELETE FROM without WHERE) and logs every blocked attempt.
#
# Installation:
#   Install this script into ~/.claude/hooks/blocker.sh and configure
#   your .claude/settings.json to reference it.
#
#   Example settings.json entry:
#     {
#       "hooks": {
#         "PreToolUse": [
#           {
#             "matcher": "Bash",
#             "hooks": [
#               {
#                 "type": "command",
#                 "command": "\"$HOME/.claude/hooks/blocker.sh\"",
#                 "timeout": 10
#               }
#             ]
#           }
#         ]
#       }
#     }
#
# Input:  JSON on stdin (PreToolUse event)
# Output: JSON on stdout to deny dangerous commands, or exit 0 to allow
# ============================================================================

set -euo pipefail

# ---- Configuration ---------------------------------------------------------
LOGFILE="$HOME/.claude/hooks/blocked.log"

# ---- Danger detection (pure bash) ------------------------------------------
# Returns 0 (true) if the command matches a dangerous pattern, 1 otherwise.
is_dangerous() {
  local cmd="$1"

  # 1) rm -rf (and variants: rm -fr, rm --recursive --force, etc.)
  if printf '%s' "$cmd" | grep -Eq '\brm\s+(-[-a-zA-Z]*[rR][-a-zA-Z]*[fF][-a-zA-Z]*|-[a-zA-Z]*rf[a-zA-Z]*|-[a-zA-Z]*fr[a-zA-Z]*)\b'; then
    return 0
  fi

  # Normalize to lowercase for SQL keyword matching
  local lower_cmd
  lower_cmd="$(printf '%s' "$cmd" | tr '[:upper:]' '[:lower:]')"

  # 2) DROP TABLE (SQL destructive)
  if printf '%s' "$lower_cmd" | grep -Eq '\bdrop\s+table\b'; then
    return 0
  fi

  # 3) git push --force or git push -f
  if printf '%s' "$lower_cmd" | grep -Eq '\bgit\s+push\s+.*(--force|-f)\b'; then
    return 0
  fi

  # 4) TRUNCATE [TABLE] (SQL destructive)
  if printf '%s' "$lower_cmd" | grep -Eq '\btruncate(\s+table)?\b'; then
    return 0
  fi

  # 5) DELETE FROM without WHERE
  if printf '%s' "$lower_cmd" | grep -Eq '\bdelete\s+from\b'; then
    if ! printf '%s' "$lower_cmd" | grep -Eq '\bwhere\b'; then
      return 0
    fi
  fi

  return 1
}

# ---- JSON extraction using Python3 (no jq dependency) ----------------------
extract_json_field() {
  local field="$1"
  python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Support dot-notation like 'tool_input.command'
    parts = '$field'.split('.')
    val = data
    for p in parts:
        val = val.get(p, '')
        if val is None:
            val = ''
    if isinstance(val, str):
        sys.stdout.write(val)
    else:
        sys.stdout.write(str(val))
except Exception:
    sys.stdout.write('')
" 2>/dev/null
}

emit_deny_json() {
  local reason="$1"
  python3 -c "
import sys, json
output = {
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': '$reason'
    }
}
json.dump(output, sys.stdout, indent=2)
"
}

# ---- Logging ---------------------------------------------------------------
log_blocked() {
  local ts cmd cwd
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  cmd="$1"
  cwd="$2"
  mkdir -p "$(dirname "$LOGFILE")"
  printf '[%s] BLOCKED | cmd=%s | cwd=%s\n' "$ts" "$cmd" "$cwd" >> "$LOGFILE"
}

# ---- Main ------------------------------------------------------------------
main() {
  # Read all of stdin (JSON from Claude Code)
  local input
  input="$(cat)"

  # Extract fields using Python
  local tool_name tool_input_command cwd
  tool_name="$(printf '%s' "$input" | extract_json_field 'tool_name')"
  tool_input_command="$(printf '%s' "$input" | extract_json_field 'tool_input.command')"
  cwd="$(printf '%s' "$input" | extract_json_field 'cwd')"

  # Defaults
  tool_name="${tool_name:-unknown}"
  tool_input_command="${tool_input_command:-}"
  cwd="${cwd:-unknown}"

  # Only process Bash tool calls
  if [ "$tool_name" != "Bash" ]; then
    exit 0
  fi

  # Skip empty commands
  if [ -z "$tool_input_command" ]; then
    exit 0
  fi

  # Check if the command is dangerous
  if is_dangerous "$tool_input_command"; then
    # Log the blocked attempt
    log_blocked "$tool_input_command" "$cwd"

    # Output JSON decision to deny the tool call
    emit_deny_json "Blocked by security hook: dangerous command detected"
    exit 0
  fi

  # Allow the command — exit 0 with no stdout means pass-through
  exit 0
}

main "$@"
