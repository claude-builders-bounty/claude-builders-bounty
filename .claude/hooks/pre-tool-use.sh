#!/bin/bash
# Pre-tool-use hook for Claude Code - Block destructive bash commands
# Place in .claude/hooks/pre-tool-use.sh
# Reference in .claude/settings.json: { "hooks": { "pre_tool_use": ".claude/hooks/pre-tool-use.sh" } }

set -euo pipefail

# Blocklist: patterns that are considered destructive
BLOCKLIST=(
  "rm -rf /"
  "rm -rf --no-preserve-root"
  "rm -rf /*"
  "mkfs\\."
  "dd if="
  "dd of="
  ":(){ :|:& };:"
  "fork.bomb"
  "> /dev/sda"
  "> /dev/hda"
  "poweroff"
  "halt"
  "reboot"
  "shutdown -h"
  "shutdown -r"
  "chmod 000 /"
  "chown -R 0:0 /"
  "mv / /dev/null"
  "wget.*--post-file"
  "curl.*--data.*@/"
  "git push --force"
  "git push -f"
  "DROP DATABASE"
  "DROP TABLE"
  "TRUNCATE TABLE"
  "DELETE FROM.*WHERE 1=1"
  "pg_dump.*--clean"
)

# Allowlist: commands that are always safe
ALLOWLIST=(
  "rm -rf .git"
  "rm -rf node_modules"
  "rm -rf dist"
  "rm -rf build"
  "rm -rf .next"
  "rm -rf target"
  "rm -rf __pycache__"
  "rm -rf .cache"
  "git push --force-with-lease"
)

BYPASS_MARKER="__I_KNOW_WHAT_IM_DOING__"

# Read the JSON input from stdin
INPUT=$(cat)

# Extract the bash command from the JSON input
COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/"command"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')

# Check if bypass marker is present
if echo "$COMMAND" | grep -q "$BYPASS_MARKER"; then
  # Remove the bypass marker and allow
  exit 0
fi

# Check allowlist first
for safe in "${ALLOWLIST[@]}"; do
  if echo "$COMMAND" | grep -qE "$safe"; then
    exit 0
  fi
done

# Check blocklist
for dangerous in "${BLOCKLIST[@]}"; do
  if echo "$COMMAND" | grep -qE "$dangerous"; then
    echo "{\"error\":\"BLOCKED: Destructive command detected. If you really want to run this, prefix with: $BYPASS_MARKER\",\"command\":\"$COMMAND\",\"matched_pattern\":\"$dangerous\"}"
    exit 1
  fi
done

# Default: allow
exit 0
