#!/usr/bin/env bash
# bash-safety-hook.sh — Pre-tool-use hook that blocks destructive bash commands
# For use with Claude Code's hook system
#
# Install: Add to .claude/settings.json under hooks.pre_tool_use
# License: MIT

set -euo pipefail

# Read the tool use event from stdin (JSON)
INPUT=$(cat)

# Extract tool name and command
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Only check Bash tool calls
if [ "$TOOL_NAME" != "Bash" ]; then
  echo '{"decision": "approve"}'
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  echo '{"decision": "approve"}'
  exit 0
fi

# Normalize: lowercase for pattern matching
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

BLOCKED=false
REASON=""

# === DESTRUCTIVE FILE OPERATIONS ===
if echo "$CMD_LOWER" | grep -qP 'rm\s+(-[a-z]*f[a-z]*\s+|.*--force)'; then
  BLOCKED=true
  REASON="Blocked: rm with --force/-f flag detected"
fi

if echo "$CMD_LOWER" | grep -qP 'rm\s+-[a-z]*r[a-z]*f|rm\s+-[a-z]*fr'; then
  BLOCKED=true
  REASON="Blocked: rm -rf detected — recursive force delete"
fi

if echo "$CMD_LOWER" | grep -qP '>\s*/dev/sd[a-z]|dd\s+.*of=/dev/'; then
  BLOCKED=true
  REASON="Blocked: Direct disk write operation detected"
fi

if echo "$CMD_LOWER" | grep -qP 'mkfs\.|format\s+'; then
  BLOCKED=true
  REASON="Blocked: Filesystem format operation detected"
fi

# === DESTRUCTIVE GIT OPERATIONS ===
if echo "$CMD_LOWER" | grep -qP 'git\s+push\s+.*--force|git\s+push\s+-f\b'; then
  BLOCKED=true
  REASON="Blocked: git push --force can overwrite remote history"
fi

if echo "$CMD_LOWER" | grep -qP 'git\s+reset\s+--hard'; then
  BLOCKED=true
  REASON="Blocked: git reset --hard discards all uncommitted changes"
fi

if echo "$CMD_LOWER" | grep -qP 'git\s+clean\s+-[a-z]*f'; then
  BLOCKED=true
  REASON="Blocked: git clean -f removes untracked files permanently"
fi

if echo "$CMD_LOWER" | grep -qP 'git\s+checkout\s+--\s+\.'; then
  BLOCKED=true
  REASON="Blocked: git checkout -- . discards all unstaged changes"
fi

if echo "$CMD_LOWER" | grep -qP 'git\s+branch\s+-D\b'; then
  BLOCKED=true
  REASON="Blocked: git branch -D force-deletes branch without merge check"
fi

if echo "$CMD_LOWER" | grep -qP 'git\s+stash\s+drop'; then
  BLOCKED=true
  REASON="Blocked: git stash drop permanently removes stashed changes"
fi

# === DATABASE DESTRUCTIVE OPERATIONS ===
if echo "$CMD_LOWER" | grep -qP 'drop\s+(table|database|schema|index)'; then
  BLOCKED=true
  REASON="Blocked: SQL DROP operation detected"
fi

if echo "$CMD_LOWER" | grep -qP 'truncate\s+table'; then
  BLOCKED=true
  REASON="Blocked: SQL TRUNCATE TABLE detected"
fi

if echo "$CMD_LOWER" | grep -qP 'delete\s+from\s+\w+\s*;?\s*$|delete\s+from\s+\w+\s+where\s+1\s*=\s*1'; then
  BLOCKED=true
  REASON="Blocked: DELETE without meaningful WHERE clause"
fi

# === PROCESS KILLING ===
if echo "$CMD_LOWER" | grep -qP 'kill\s+-9|killall|pkill\s+-9'; then
  BLOCKED=true
  REASON="Blocked: Forceful process termination (kill -9/killall)"
fi

# === SYSTEM MODIFICATION ===
if echo "$CMD_LOWER" | grep -qP 'chmod\s+-R\s+777|chmod\s+777\s+/'; then
  BLOCKED=true
  REASON="Blocked: chmod 777 on system paths — security risk"
fi

if echo "$CMD_LOWER" | grep -qP 'chown\s+-R.*\s+/(?!home|tmp)'; then
  BLOCKED=true
  REASON="Blocked: Recursive chown on system directories"
fi

# === CREDENTIAL/SECRET EXPOSURE ===
if echo "$CMD_LOWER" | grep -qP 'cat\s+.*\.env|cat\s+.*credentials|cat\s+.*\.ssh/'; then
  BLOCKED=true
  REASON="Blocked: Reading sensitive credential files"
fi

if echo "$CMD_LOWER" | grep -qP 'curl\s+.*\|\s*(ba)?sh|wget\s+.*\|\s*(ba)?sh'; then
  BLOCKED=true
  REASON="Blocked: Piping remote content directly to shell"
fi

# === OUTPUT DECISION ===
if [ "$BLOCKED" = true ]; then
  # Output JSON that Claude Code's hook system expects
  jq -n --arg reason "$REASON" '{"decision": "block", "reason": $reason}'
  exit 0
else
  echo '{"decision": "approve"}'
  exit 0
fi
