#!/usr/bin/env bash
# PreToolUse hook for Claude Code — blocks destructive bash commands.
# Target path: ~/.claude/hooks/pre-tool-use.sh
# See: https://code.claude.com/docs/en/hooks
#
# Reads the hook payload from stdin, inspects tool_input.command, and emits a
# permissionDecision of "deny" only for the dangerous patterns below. Any other
# command (and any payload we cannot parse) exits 0 untouched, so the hook never
# gets in the way of normal work.

set -uo pipefail

INPUT=$(cat)

# Extract .tool_input.command without requiring a specific runtime. Prefer
# python3 (handles quoting correctly), fall back to jq. If neither is installed
# we deliberately fail open: a missing JSON parser must not block every command.
extract_command() {
  # `command -v python3` also succeeds for the Windows Store stub, which exits
  # non-zero and prints an install prompt, so probe each interpreter for real.
  local py
  for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1 && "$py" -c 'pass' >/dev/null 2>&1; then
      printf '%s' "$INPUT" | "$py" -c '
import json, sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
except Exception:
    pass
' 2>/dev/null
      return
    fi
  done
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null
  fi
}

COMMAND=$(extract_command)
if [[ -z "${COMMAND//[[:space:]]/}" ]]; then
  exit 0
fi

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"

block() {
  local reason="$1"
  local ts pwd_path
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  pwd_path=$(pwd 2>/dev/null || echo "unknown")
  mkdir -p "$LOG_DIR"
  printf '%s\t%s\t%s\t%s\n' "$ts" "$COMMAND" "$pwd_path" "$reason" >> "$LOG_FILE"
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
  exit 0
}

# rm recursive + force, in any flag order: rm -rf, rm -fr, rm -Rf, rm -r -f,
# rm -f -r, rm --recursive --force, rm --force --recursive.
if printf '%s' "$COMMAND" | grep -qiE \
  'rm[[:space:]]+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*|-[r][[:space:]]+-f|-f[[:space:]]+-r|--recursive[[:space:]]+--force|--force[[:space:]]+--recursive)([[:space:]]|$)'; then
  block "Recursive force delete (rm -rf) blocked"
fi

# SQL DROP TABLE / DROP TABLE IF EXISTS.
if printf '%s' "$COMMAND" | grep -qiE 'drop[[:space:]]+table([[:space:]]|$)'; then
  block "SQL DROP TABLE blocked"
fi

# SQL TRUNCATE, with or without the optional TABLE keyword.
if printf '%s' "$COMMAND" | grep -qiE 'truncate[[:space:]]+(table[[:space:]]+)?[[:alnum:]_."`]'; then
  block "SQL TRUNCATE blocked"
fi

# SQL DELETE FROM without any WHERE clause.
if printf '%s' "$COMMAND" | grep -qiE 'delete[[:space:]]+from[[:space:]]+[^;]+' \
  && ! printf '%s' "$COMMAND" | grep -qiE 'where[[:space:]]'; then
  block "SQL DELETE FROM without WHERE blocked"
fi

# git push --force / -f. --force-with-lease is intentionally allowed: it
# refuses to overwrite work that was pushed after the local ref was fetched.
if printf '%s' "$COMMAND" | grep -qiE 'git[[:space:]]+push([[:space:]]+[^;&|]*)?[[:space:]](--force([[:space:]]|$)|-f([[:space:]]|$))'; then
  block "Git force push (git push --force / -f) blocked"
fi

# Extra high-risk patterns: filesystem creation and raw block-device writes.
if printf '%s' "$COMMAND" | grep -qiE 'mkfs(\.[a-z0-9]+)?[[:space:]]'; then
  block "Filesystem creation (mkfs) blocked"
fi
if printf '%s' "$COMMAND" | grep -qiE 'dd[[:space:]]+[^;&|]*[[:space:]]of=/dev/'; then
  block "Raw block-device overwrite (dd of=/dev/...) blocked"
fi

# Everything else passes through untouched.
exit 0
