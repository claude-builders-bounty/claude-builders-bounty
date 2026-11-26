#!/bin/sh
# Bash fallback for the destructive-command PreToolUse hook.
# Preferred path: exec the Python hook (same stdin/stdout JSON protocol).
# If python3 is unavailable, fall back to a grep-based check and exit 2
# (Claude Code treats a non-zero exit from a PreToolUse hook as a block).
# Usage: registered as the PreToolUse hook command instead of the .py file.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/block-destructive-commands.py"
fi
# --- grep fallback (no Python) ---
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
# shellcheck disable=SC2015
if printf '%s' "$CMD" | grep -Eq 'rm[[:space:]]+-[a-z]*r[a-z]*f|rm[[:space:]]+-[a-z]*f[a-z]*r|DROP[[:space:]]+TABLE|TRUNCATE|git[[:space:]]+push[[:space:]]+.*(--force| -f)([[:space:]]|$)' \
  || printf '%s' "$CMD" | grep -Eqi 'DELETE[[:space:]]+FROM[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[[:space:]]*$'; then
  mkdir -p ~/.claude/hooks
  printf '%s | cwd=%s | reason=%s | command=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${PWD:-}" "destructive command (bash fallback)" "$CMD" >> ~/.claude/hooks/blocked.log
  printf 'Blocked destructive command (bash fallback check).\n' >&2
  exit 2
fi
exit 0
