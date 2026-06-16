#!/usr/bin/env bash
# ============================================================================
# pre_tool_use_hook.sh  —  Block dangerous bash commands before they run
#
# A safety hook for Claude Code / AI agent tool-use pipelines that
# inspects every command against a known list of destructive patterns.
# If a match is found the command is rejected before it reaches the shell.
#
# Usage:
#   source ./pre_tool_use_hook.sh
#   pre_tool_use_hook "rm -rf /"          # blocks
#   pre_tool_use_hook "ls -la"            # passes
#
# Configurable allowlist:
#   export PRE_TOOL_USE_ALLOWLIST="rsync dd_rescue"
#   export PRE_TOOL_USE_ALLOWLIST_FILE="/path/to/allowlist.txt"
#
# Author:   SiddhantOfficial
# License:  MIT (same as repo)
# ============================================================================

# ---- Configuration ---------------------------------------------------------

HOOK_MODE="${PRE_TOOL_USE_HOOK_MODE:-strict}"
ALLOWLIST_FILE="${PRE_TOOL_USE_ALLOWLIST_FILE:-}"
ALLOWLIST="${PRE_TOOL_USE_ALLOWLIST:-}"

# ---- Destructive patterns (regex) -----------------------------------------

BLOCKED_PATTERNS=(
  # 1. Recursive / or ~ deletion
  'rm[[:space:]]+-[rf]+[[:space:]]+/[[:space:]]*$'
  'rm[[:space:]]+-[rf]+[[:space:]]+~[[:space:]]*$'
  'rm[[:space:]]+-[rf]+[[:space:]]+/\*'
  'rm[[:space:]]+-[rf]+[[:space:]]+~/\*'
  'rm[[:space:]]+-[rf]+[[:space:]]+/[[:space:]]+\*'

  # 2. SQL destructive operations
  'drop[[:space:]]+table'
  'drop[[:space:]]+database'
  'truncate[[:space:]]+table'

  # 3. Git force-push to protected branches
  'git[[:space:]]+push[[:space:]]+.*--force'
  'git[[:space:]]+push[[:space:]]+.*-f[[:space:]]+origin[[:space:]]+main'
  'git[[:space:]]+push[[:space:]]+.*-f[[:space:]]+origin[[:space:]]+master'

  # 4. Recursive permission nuke
  'chmod[[:space:]]+-[Rr]+[[:space:]]+777[[:space:]]+/'
  'chmod[[:space:]]+-[Rr]+[[:space:]]+777[[:space:]]+~'

  # 5. dd destructive patterns
  'dd[[:space:]]+if='
  'dd[[:space:]]+of=/dev/[a-z]+'

  # 6. Fork bomb
  ':\(\)[[:space:]]*\{[[:space:]]*:[|:&][[:space:]]*\};[[:space:]]*:'

  # 7. Remote pipe-to-shell (wget/curl | bash/sh)
  'wget[[:space:]]+.*\|[[:space:]]*bash'
  'wget[[:space:]]+.*\|[[:space:]]*sh[[:space:]]*$'
  'curl[[:space:]]+.*\|[[:space:]]*bash'
  'curl[[:space:]]+.*\|[[:space:]]*sh[[:space:]]*$'
  'curl[[:space:]]+.*\|[[:space:]]*sudo[[:space:]]+bash'

  # 8. eval with remote source
  'eval[[:space:]]*"\$\(curl'
  'eval[[:space:]]*"\$\(wget'

  # 9. Filesystem formatting
  'mkfs\.[a-z]+[[:space:]]+/dev/'
  'mkfs[[:space:]]+/dev/'
  'format[[:space:]]+/dev/'
  'mkfs[[:space:]]+-t'

  # 10. Unsafe redirects that clobber system files
  '>[[:space:]]*/etc/'
  '>[[:space:]]*/boot/'
  '>[[:space:]]*/dev/'

  # 11. Mass chown on root-owned paths
  'chown[[:space:]]+-[Rr]+[[:space:]]+[0-9]+[[:space:]]+/'
  'chown[[:space:]]+-[Rr]+[[:space:]]+[a-z_]+[[:space:]]+/'

  # 12. Shutdown / reboot
  'halt[[:space:]]*$'
  'poweroff[[:space:]]*$'
  'reboot[[:space:]]*$'
)

# ---- Helper Functions ------------------------------------------------------

_pre_tool_use_normalize() {
  echo "$1" | sed -E 's/[[:space:]]+/ /g' | sed -E 's/^[[:space:]]+|[[:space:]]+$//g'
}

_pre_tool_use_is_allowed() {
  local cmd="$1"
  local normalized
  normalized="$(_pre_tool_use_normalize "$cmd")"
  local first_word
  first_word="${normalized%% *}"

  local allow_entry
  if [ -n "$ALLOWLIST" ]; then
    for allow_entry in $ALLOWLIST; do
      if [ "$first_word" = "$allow_entry" ]; then
        return 0
      fi
    done
  fi

  if [ -n "$ALLOWLIST_FILE" ] && [ -f "$ALLOWLIST_FILE" ]; then
    while IFS= read -r allow_entry; do
      allow_entry="$(echo "$allow_entry" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
      [ -z "$allow_entry" ] && continue
      [ "${allow_entry###}" != "$allow_entry" ] && continue
      if [ "$first_word" = "$allow_entry" ]; then
        return 0
      fi
    done < "$ALLOWLIST_FILE"
  fi

  if [ -n "$ALLOWLIST_FILE" ] && [ -f "$ALLOWLIST_FILE" ]; then
    while IFS= read -r allow_entry; do
      allow_entry="$(echo "$allow_entry" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
      [ -z "$allow_entry" ] && continue
      [ "${allow_entry###}" != "$allow_entry" ] && continue
      if [ "${normalized#"$allow_entry"}" != "$normalized" ]; then
        return 0
      fi
    done < "$ALLOWLIST_FILE"
  fi

  return 1
}

_pre_tool_use_is_blocked() {
  local raw_cmd="$1"
  local cmd
  cmd="$(_pre_tool_use_normalize "$raw_cmd")"
  local lower_cmd
  lower_cmd="$(echo "$cmd" | tr '[:upper:]' '[:lower:]')"

  local pattern
  for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$lower_cmd" | grep -qE "$pattern"; then
      return 0
    fi
  done

  return 1
}

# ---- Main Entry Point ------------------------------------------------------

pre_tool_use_hook() {
  local raw_cmd="$1"

  if [ -z "$raw_cmd" ]; then
    echo "pre_tool_use_hook: OK (empty command)"
    return 0
  fi

  if _pre_tool_use_is_allowed "$raw_cmd"; then
    echo "pre_tool_use_hook: ALLOWED (on allowlist)"
    return 0
  fi

  if _pre_tool_use_is_blocked "$raw_cmd"; then
    echo "pre_tool_use_hook: BLOCKED -- dangerous command rejected"
    echo "  Command: $raw_cmd"
    echo "  To allow it, add to ALLOWLIST (env var) or ${ALLOWLIST_FILE:-allowlist.txt}"
    return 1
  fi

  if [ "$HOOK_MODE" = "strict" ]; then
    local lower_cmd
    lower_cmd="$(echo "$(_pre_tool_use_normalize "$raw_cmd")" | tr '[:upper:]' '[:lower:]')"
    local suspicious=0

    if echo "$lower_cmd" | grep -qE '^sudo[[:space:]]+(rm|dd|mkfs|chmod|chown|format)'; then
      suspicious=1
    fi

    if echo "$lower_cmd" | grep -qE '(>|>>)[[:space:]]*/etc/'; then
      suspicious=1
    fi

    if [ $suspicious -eq 1 ]; then
      echo "pre_tool_use_hook: SUSPICIOUS (strict mode) -- review carefully"
      echo "  Command: $raw_cmd"
    fi
  fi

  echo "pre_tool_use_hook: OK"
  return 0
}

# ---- Auto-run if executed directly (not sourced) ---------------------------
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ $# -eq 0 ]; then
    echo "Usage: source $0 && pre_tool_use_hook \"<command>\""
    echo "   or: $0 \"<command>\""
    exit 1
  fi
  pre_tool_use_hook "$1"
  exit $?
fi
