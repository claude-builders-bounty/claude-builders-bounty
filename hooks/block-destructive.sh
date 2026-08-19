#!/usr/bin/env bash
# block-destructive.sh — Pre-tool-use hook that blocks dangerous bash commands
# Install: cp block-destructive.sh ~/.claude/hooks/block-destructive.sh
#         chmod +x ~/.claude/hooks/block-destructive.sh
#
# Then add to your Claude Code settings (~/.claude/settings.json):
#   { "hooks": { "pre-tool-use": [{ "command": "bash ~/.claude/hooks/block-destructive.sh" }] } }
#
# Or install in 2 commands:
#   mkdir -p ~/.claude/hooks && cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh

set -euo pipefail

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
PROJECT_PATH="${PWD}"
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

# Read command from stdin (Claude Code sends the tool input as JSON on stdin)
INPUT=$(cat)

# Extract the 'command' field from the JSON input
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  # No command found — allow (not a bash execution)
  exit 0
fi

# --- Dangerous patterns ---
# 1. rm -rf (force recursive delete)
# 2. DROP TABLE / TRUNCATE / DELETE FROM without WHERE
# 3. git push --force / --force-with-lease to main/master
# 4. FORMAT / ERASE at disk level
# 5. chmod 777 on / or system dirs
# 6. dd if=/dev/zero destructive writes
# 7. > /dev/sda or similar direct disk writes
# 8. mkfs.* (format filesystem)

BLOCKED=0
REASON=""

# Normalized command for matching (lowercase, collapse whitespace)
CMD_NORM=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ')

# Pattern: rm -rf / or rm -rf without safeguards
if echo "$CMD_NORM" | grep -qP '(^|\s)rm\s+(-[a-zA-Z]*f[a-zA-Z]*|--force)\s+(-[a-zA-Z]*r[a-zA-Z]*|--recursive|/)'; then
  # Allow if targeting specific safe paths only (node_modules, .next, dist, build, __pycache__)
  if ! echo "$CMD_NORM" | grep -qP 'rm.*(-f.*-r|-r.*-f).*(node_modules|\.next|dist|build|__pycache__|\.cache|coverage)'; then
    BLOCKED=1
    REASON="rm -rf detected: force-recursive delete can destroy files irreversibly"
  fi
fi

# Pattern: DROP TABLE / TRUNCATE / DELETE FROM without WHERE
if echo "$CMD_NORM" | grep -qP '(^|\s)(drop\s+table|truncate\s+table?)'; then
  BLOCKED=1
  REASON="SQL destructive command detected (DROP TABLE / TRUNCATE) without safety check"
fi

if echo "$CMD_NORM" | grep -qP 'delete\s+from' && ! echo "$CMD_NORM" | grep -qP 'where\s'; then
  BLOCKED=1
  REASON="DELETE FROM without WHERE clause detected: would delete all rows"
fi

# Pattern: git push --force to protected branches
if echo "$CMD_NORM" | grep -qP 'git\s+push.*(\-\-force|\-f)'; then
  if echo "$CMD_NORM" | grep -qP '(main|master|prod|release)'; then
    BLOCKED=1
    REASON="git push --force to a protected branch (main/master/prod/release) is blocked"
  fi
fi

# Pattern: direct disk destructive writes
if echo "$CMD_NORM" | grep -qP '(>|>>|\s)/dev/sd[a-z]|dd\s+.*of=/dev/'; then
  BLOCKED=1
  REASON="Direct disk write detected: can destroy filesystem"
fi

# Pattern: chmod 777 on system directories
if echo "$CMD_NORM" | grep -qP 'chmod\s+777\s+(/|/usr|/etc|/bin|/var|/home)'; then
  BLOCKED=1
  REASON="chmod 777 on system directory detected: security risk"
fi

# Pattern: filesystem format
if echo "$CMD_NORM" | grep -qP 'mkfs|format\s+(c:|d:|/dev/)'; then
  BLOCKED=1
  REASON="Filesystem format command detected: would destroy all data on target"
fi

# --- Take action ---
if [ "$BLOCKED" -eq 1 ]; then
  # Log the blocked attempt
  mkdir -p "$LOG_DIR"
  echo "[${TIMESTAMP}] BLOCKED | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"

  # Output structured response that Claude will see
  cat <<EOF
{
  "decision": "block",
  "reason": "${REASON}"
}
EOF
  exit 2
fi

# Allow the command
exit 0
