#!/usr/bin/env bash
#
# block-destructive.sh — Pre-tool-use hook that blocks dangerous bash commands.
#
# Install: see README.md (2 commands)
#
# Reads JSON input from stdin (Claude Code PreToolUse format),
# checks the bash command against dangerous patterns, and returns
# a deny decision if matched. All blocked attempts are logged.
#
set -euo pipefail

# ── read input from Claude Code ──
INPUT="$(cat)"
TOOL_NAME="$(echo "$INPUT" | jq -r '.tool_name // empty')"
COMMAND="$(echo "$INPUT" | jq -r '.tool_input.command // empty')"

# Only care about Bash tool calls
if [ "$TOOL_NAME" != "Bash" ] || [ -z "$COMMAND" ]; then
  exit 0  # not a bash command, allow
fi

# ── normalize for matching ──
LOWER="$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')"

# ── dangerous pattern definitions ──
blocked=false
reason=""

# 1) rm -rf (any path, including rm -r -f variants)
if echo "$LOWER" | grep -qE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|-[a-zA-Z]*r[a-zA-Z]*\s+)'; then
  blocked=true
  reason="'rm -rf' or variant detected — recursive force delete is not allowed"
fi

# 2) DROP TABLE / DROP DATABASE
if echo "$LOWER" | grep -qE '\bdrop\s+(table|database|schema)\b'; then
  blocked=true
  reason="'DROP TABLE/DATABASE/SCHEMA' detected — destructive SQL DDL is not allowed"
fi

# 3) TRUNCATE TABLE
if echo "$LOWER" | grep -qE '\btruncate\b'; then
  blocked=true
  reason="'TRUNCATE' detected — this will wipe table data without a WHERE clause"
fi

# 4) DELETE FROM without WHERE clause
if echo "$LOWER" | grep -qE '\bdelete\s+from\b' && ! echo "$LOWER" | grep -qE '\bwhere\b'; then
  blocked=true
  reason="'DELETE FROM' without a WHERE clause detected — this would delete all rows"
fi

# 5) git push --force / git push -f
if echo "$LOWER" | grep -qE 'git\s+push\s+.*(--force|-f\b)'; then
  blocked=true
  reason="'git push --force' detected — force pushing rewrites shared history"
fi

# 6) DELETE FROM with WHERE but suspiciously broad (optional, extra safety)
#    e.g., DELETE FROM users WHERE 1=1
if echo "$LOWER" | grep -qE '\bdelete\s+from\s+\w+\s+where\s+1\s*=\s*1'; then
  blocked=true
  reason="'DELETE FROM ... WHERE 1=1' detected — tautological WHERE clause deletes all rows"
fi

# ── handle result ──
if [ "$blocked" = true ]; then
  # Log the blocked attempt
  LOG_DIR="${HOME}/.claude/hooks"
  LOG_FILE="${LOG_DIR}/blocked.log"
  TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  
  mkdir -p "$LOG_DIR"
  printf '[%s] BLOCKED | project=%s | command=%s | reason=%s\n' \
    "$TIMESTAMP" "$PROJECT_DIR" "$COMMAND" "$reason" >> "$LOG_FILE"

  # Return deny decision to Claude Code
  jq -n \
    --arg r "$reason" \
    '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $r
      }
    }'
  exit 0
fi

# ── command is safe, allow ──
exit 0
