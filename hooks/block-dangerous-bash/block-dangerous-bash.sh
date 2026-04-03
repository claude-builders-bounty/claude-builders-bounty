#!/bin/bash
# ============================================================
# Claude Code Pre-Tool-Use Hook: Block Dangerous Bash Commands
# ============================================================
# Intercepts Bash tool calls and blocks destructive patterns
# before they execute. Logs all blocked attempts.
#
# Patterns blocked:
#   - rm -rf (recursive + forced removal, especially on / ~ $HOME)
#   - git push --force / git reset --hard / git checkout -- . / git clean -fd
#   - sudo commands
#   - Pipe to shell (curl|sh, wget|bash, etc.)
#   - Inline interpreter execution (python -c, node -e, ruby -e, perl -e)
#   - Reading secrets (.env, .pem, .key, SSH keys, credentials)
#   - SQL destructive: DROP TABLE, DROP DATABASE, TRUNCATE, DELETE FROM without WHERE
#
# Output format (stdout):
#   {"decision": "block", "reason": "..."} — to block
#   {"decision": "allow"}                  — to allow (or just exit 0)
#
# Blocked commands are logged to: ~/.claude/hooks/blocked.log
#
# Installation:
#   See README.md in this directory, or run: bash install.sh
# ============================================================

set -euo pipefail

# ---- Configuration ----------------------------------------
LOG_FILE="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="${PWD}"

# ---- Read stdin -------------------------------------------
INPUT=$(cat 2>/dev/null || true)
[ -z "$INPUT" ] && exit 0

# ---- Extract tool_name (no jq required) -------------------
TOOL_NAME=$(printf '%s' "$INPUT" | grep -o '"tool_name"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:.*"\([^"]*\)"/\1/')
[ "$TOOL_NAME" != "Bash" ] && exit 0

# ---- Extract command ---------------------------------------
# Handles both simple and escaped-string JSON values
COMMAND=$(printf '%s' "$INPUT" | grep -o '"command"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:.*"\([^"]*\)"/\1/')

# FAIL-CLOSED: if we can't parse the command, block it
if [ -z "$COMMAND" ]; then
  printf '{"decision": "block", "reason": "Could not parse command from tool input. Fail-closed for safety."}\n'
  exit 0
fi

# ---- Helper: log and block --------------------------------
block() {
  local reason="$1"

  # Ensure log directory exists
  mkdir -p "$(dirname "$LOG_FILE")"

  # Append structured JSON log entry
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local escaped_cmd
  escaped_cmd=$(printf '%s' "$COMMAND" | sed 's/\\/\\\\/g; s/"/\\"/g; s/$/\\n/g' | tr -d '\n' | sed 's/\\n$//')
  local escaped_reason
  escaped_reason=$(printf '%s' "$reason" | sed 's/"/\\"/g')
  local escaped_project
  escaped_project=$(printf '%s' "$PROJECT_PATH" | sed 's/"/\\"/g')

  printf '{"timestamp":"%s","project_path":"%s","command":"%s","reason":"%s"}\n' \
    "$timestamp" "$escaped_project" "$escaped_cmd" "$escaped_reason" \
    >> "$LOG_FILE" 2>/dev/null || true

  # Output block decision to stdout (Claude Code reads this)
  local escaped_reason_json
  escaped_reason_json=$(printf '%s' "$reason" | sed 's/"/\\"/g')
  printf '{"decision": "block", "reason": "%s"}\n' "$escaped_reason_json"
  exit 0
}

# ---- Pattern Checks ----------------------------------------

# 1. rm with recursive + force flags (especially targeting / ~ $HOME)
if printf '%s' "$COMMAND" | grep -qE '\brm\b'; then
  if printf '%s' "$COMMAND" | grep -qE '(\s|^)-[a-zA-Z]*[rR]|\s--recursive'; then
    if printf '%s' "$COMMAND" | grep -qE '(\s|^)-[a-zA-Z]*[fF]|\s--force'; then
      block "rm -rf detected. Recursive forced removal is not allowed. Use targeted deletion instead."
    fi
  fi
fi

# 2. git push --force (any variant: --force, -f, --force-with-lease)
if printf '%s' "$COMMAND" | grep -qE 'git\s+push\b.*(\s--force\b|\s-f\b|\s--force-with-lease\b)'; then
  block "git push --force detected. Force-push rewrites history and can cause irreversible data loss."
fi

# 3. git reset --hard
if printf '%s' "$COMMAND" | grep -qE 'git\s+reset\b.*\s--hard\b'; then
  block "git reset --hard detected. This permanently discards uncommitted changes."
fi

# 4. git checkout -- . (discard all working tree changes)
if printf '%s' "$COMMAND" | grep -qE 'git\s+checkout\b.*--\s+\.'; then
  block "git checkout -- . detected. This discards all unstaged changes in the working tree."
fi

# 5. git clean -fd (remove untracked files)
if printf '%s' "$COMMAND" | grep -qE 'git\s+clean\b.*-[a-zA-Z]*[fF]'; then
  block "git clean -f detected. This permanently deletes untracked files."
fi

# 6. sudo
if printf '%s' "$COMMAND" | grep -qE '(^|\s)sudo\s'; then
  block "sudo detected. Elevated privilege commands are not allowed."
fi

# 7. Pipe to shell (curl|sh, wget|bash, cat|bash, etc.)
if printf '%s' "$COMMAND" | grep -qE '\|\s*(bash|sh|zsh|fish|ksh)\b'; then
  block "Pipe to shell detected (e.g. curl|bash). This allows arbitrary remote code execution."
fi

# 8. Inline interpreter one-liners (python -c, node -e, ruby -e, perl -e)
if printf '%s' "$COMMAND" | grep -qE '(python3?|node|nodejs|ruby|perl)\s+-[ce]\s'; then
  block "Inline interpreter execution detected (e.g. python -c '...'). Execute code via a file instead."
fi

# 9. Reading .env files via shell readers
if printf '%s' "$COMMAND" | grep -qE '(cat|less|more|head|tail|bat|type)\s+[^\|]*\.env\b'; then
  block "Attempted to read .env file via shell. Use the Read tool instead to avoid leaking secrets."
fi

# 10. Reading .pem / .key files via shell readers
if printf '%s' "$COMMAND" | grep -qE '(cat|less|more|head|tail|bat|type)\s+[^\|]*\.(pem|key|p12|pfx)\b'; then
  block "Attempted to read a private key file (.pem/.key) via shell."
fi

# 11. Reading SSH keys
if printf '%s' "$COMMAND" | grep -qE '(cat|less|more|head|tail|bat)\s+[^\|]*\.ssh/'; then
  block "Attempted to read SSH key material via shell."
fi

# 12. Reading credentials/secrets
if printf '%s' "$COMMAND" | grep -qiE '(cat|less|more|head|tail|bat)\s+[^\|]*(credential|secret|\.aws/)'; then
  block "Attempted to read credentials or secrets via shell."
fi

# 13. SQL: DROP TABLE / DROP DATABASE
if printf '%s' "$COMMAND" | grep -qiE '\bDROP\s+(TABLE|DATABASE|SCHEMA)\b'; then
  block "SQL DROP TABLE/DATABASE detected. This permanently destroys database objects."
fi

# 14. SQL: TRUNCATE
if printf '%s' "$COMMAND" | grep -qiE '\bTRUNCATE\b'; then
  block "SQL TRUNCATE detected. This permanently deletes all rows from a table."
fi

# 15. SQL: DELETE FROM without WHERE clause
# Match DELETE FROM <table> not followed by WHERE (allowing for whitespace/newlines)
if printf '%s' "$COMMAND" | grep -qiE '\bDELETE\s+FROM\s+\S+'; then
  if ! printf '%s' "$COMMAND" | grep -qiE '\bDELETE\s+FROM\s+.*\bWHERE\b'; then
    block "SQL DELETE FROM without WHERE detected. This would delete all rows in the table."
  fi
fi

# ---- Allow -------------------------------------------------
printf '{"decision": "allow"}\n'
exit 0
