#!/usr/bin/env bash
# Pre-tool-use hook that blocks destructive bash commands.
# Reads JSON from stdin (Claude Code hook protocol), inspects the command,
# and exits non-zero with a stderr message when a destructive pattern is found.

set -euo pipefail

BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"

# ---------------------------------------------------------------------------
# Read the full JSON payload from stdin
# ---------------------------------------------------------------------------
INPUT="$(cat)"

# ---------------------------------------------------------------------------
# Only activate for Bash tool calls
# ---------------------------------------------------------------------------
TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)"

if [[ "$TOOL_NAME" != "Bash" ]]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Extract the command string
# ---------------------------------------------------------------------------
COMMAND="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)"

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Normalise the command for matching:
#   - collapse whitespace
#   - case-insensitive matching is handled per-pattern
# ---------------------------------------------------------------------------
NORMALISED="$(printf '%s' "$COMMAND" | tr '\n' ' ' | sed 's/  */ /g')"

# ---------------------------------------------------------------------------
# Helper: block and log
# ---------------------------------------------------------------------------
block() {
  local reason="$1"
  mkdir -p "$(dirname "$BLOCKED_LOG")"
  printf '[%s] BLOCKED | reason: %s | command: %s | project: %s\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    "$reason" \
    "$COMMAND" \
    "${PWD}" \
    >> "$BLOCKED_LOG"

  # Message to Claude (stderr is displayed to the model)
  cat >&2 <<EOF
BLOCKED: Destructive command detected.
Reason: $reason
Command: $COMMAND

This command has been blocked by the pre-tool-use safety hook because it
matches a known destructive pattern. If you believe this is a false positive,
ask the user to run the command manually.
EOF
  exit 1
}

# ---------------------------------------------------------------------------
# Pattern checks
# ---------------------------------------------------------------------------

# 1. rm -rf / rm -r on dangerous paths (/, /*, ~, $HOME, etc.)
#    Also catches bare "rm -rf" with no target (which defaults to error but is suspicious)
if printf '%s' "$NORMALISED" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+(-[a-zA-Z]+\s+)*)(/\s|/\*|~/|~\*|\$HOME|\$\{HOME\}|/etc|/usr|/var|/boot|/sys|/proc|/dev|/bin|/sbin|/lib|/opt)'; then
  block "rm -r on dangerous system/home path"
fi

# Catch the extremely dangerous "rm -rf /" or "rm -rf /*" specifically
if printf '%s' "$NORMALISED" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)\s+(/\s*$|/\*|/\s)'; then
  block "rm -rf on root filesystem"
fi

# 2. DROP TABLE / DROP DATABASE (case-insensitive)
if printf '%s' "$NORMALISED" | grep -iqE '\bDROP\s+(TABLE|DATABASE)\b'; then
  block "DROP TABLE/DATABASE statement"
fi

# 3. git push --force / git push -f (including variants like --force-with-lease is intentionally allowed)
if printf '%s' "$NORMALISED" | grep -qE 'git\s+push\s+.*--force(\s|$)|git\s+push\s+.*\s-f(\s|$)|git\s+push\s+-f(\s|$)'; then
  block "git push --force / git push -f"
fi

# 4. TRUNCATE TABLE (case-insensitive)
if printf '%s' "$NORMALISED" | grep -iqE '\bTRUNCATE\s+(TABLE\s+)?\w'; then
  block "TRUNCATE TABLE statement"
fi

# 5. DELETE FROM without WHERE (case-insensitive)
#    Match DELETE FROM <table> that is NOT followed by WHERE
if printf '%s' "$NORMALISED" | grep -iqE '\bDELETE\s+FROM\s+\S+'; then
  if ! printf '%s' "$NORMALISED" | grep -iqE '\bDELETE\s+FROM\s+\S+.*\bWHERE\b'; then
    block "DELETE FROM without WHERE clause"
  fi
fi

# 6. git reset --hard
if printf '%s' "$NORMALISED" | grep -qE 'git\s+reset\s+.*--hard'; then
  block "git reset --hard"
fi

# 7. git clean with -f (force) — catches -fd, -fdx, -fX, etc.
if printf '%s' "$NORMALISED" | grep -qE 'git\s+clean\s+.*-[a-zA-Z]*f'; then
  block "git clean -f (force clean)"
fi

# ---------------------------------------------------------------------------
# If we reach here, the command is allowed.
# ---------------------------------------------------------------------------
exit 0
