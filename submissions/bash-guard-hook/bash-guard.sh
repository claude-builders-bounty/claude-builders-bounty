#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Bash Guard
# Blocks destructive bash commands before execution
# 
# Claude Code hooks spec: reads JSON from stdin, outputs JSON to stdout
# Input:  { "tool": "bash", "args": { "command": "..." } }
# Output: { "continue": true } or { "continue": false, "reason": "..." }

set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Read input from stdin
INPUT=$(cat)

# Extract the command from JSON input
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    cmd = data.get('args', {}).get('command', '') or data.get('command', '')
    print(cmd)
except:
    print('')
" 2>/dev/null)

if [ -z "$COMMAND" ]; then
  echo '{"continue": true}'
  exit 0
fi

# Get project path
PROJECT_PATH="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Normalize command (lowercase, collapse spaces)
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]' | tr -s ' ')

BLOCKED=false
REASON=""

# Pattern 1: rm -rf (recursive force delete) — warn but allow common build dirs
if echo "$CMD_LOWER" | grep -qE 'rm\s+.*-rf\b|rm\s+.*-fr\b|rm\s+.*--recursive.*--force'; then
  # Allow common safe paths: /tmp, node_modules, .cache, build, dist
  if echo "$CMD_LOWER" | grep -qE '/tmp/|node_modules|\.cache/|/build/|/dist/|__pycache__'; then
    # Common cleanup patterns — allow with a note
    :
  elif echo "$CMD_LOWER" | grep -qE 'rm\s+.*-rf\s+/[^t]|rm\s+.*-rf\s+/\*|rm\s+.*-rf\s+~|rm\s+.*-rf\s+\$HOME|rm\s+.*-rf\s+/$'; then
    BLOCKED=true
    REASON="CRITICAL: Attempting to delete root/home directory"
  else
    BLOCKED=true
    REASON="Destructive delete: 'rm -rf' can permanently delete files and directories"
  fi
fi

# Pattern 2: DROP TABLE / DROP DATABASE
if echo "$CMD_LOWER" | grep -qE '\bdrop\s+(table|database)\b'; then
  BLOCKED=true
  REASON="Destructive SQL: DROP TABLE/DATABASE removes data permanently"
fi

# Pattern 3: TRUNCATE TABLE
if echo "$CMD_LOWER" | grep -qE '\btruncate\s+(table\s+)?\w+'; then
  BLOCKED=true
  REASON="Destructive SQL: TRUNCATE removes all rows without WHERE clause"
fi

# Pattern 4: DELETE FROM without WHERE
if echo "$CMD_LOWER" | grep -qE '\bdelete\s+from\s+\w+'; then
  if ! echo "$CMD_LOWER" | grep -q '\bwhere\b'; then
    BLOCKED=true
    REASON="Destructive SQL: DELETE FROM without WHERE clause would delete ALL rows"
  fi
fi

# Pattern 5: git push --force
if echo "$CMD_LOWER" | grep -qE '\bgit\s+push\s+.*--force|\bgit\s+push\s+.*-f\b'; then
  BLOCKED=true
  REASON="Destructive git: force push can overwrite remote history — use --force-with-lease instead"
fi

# Pattern 6: mkfs / dd to /dev / fdisk
if echo "$CMD_LOWER" | grep -qE '\bmkfs\.|dd\s+if=.*of=/dev|\bfdisk\s+/dev'; then
  BLOCKED=true
  REASON="CRITICAL: Disk-level operation detected — can destroy filesystems"
fi

# Pattern 7: chmod -R 777 / or chown -R /
if echo "$CMD_LOWER" | grep -qE 'chmod\s+.*-R\s+777\s+/|chown\s+.*-R\s+.*\s+/'; then
  BLOCKED=true
  REASON="Security risk: Recursive permission change on root directory"
fi

# Pattern 8: fork bomb
if echo "$CMD_LOWER" | grep -qE ':.*\(\)\s*\{\s*.*\|.*&\s*;.*\}'; then
  BLOCKED=true
  REASON="CRITICAL: Fork bomb pattern detected — will crash the system"
fi

# Pattern 9: curl/wget piped to bash/sh
if echo "$CMD_LOWER" | grep -qE '(curl|wget)\b.*\|\s*(bash|sh|zsh)'; then
  BLOCKED=true
  REASON="Security risk: Piping remote content directly to shell — inspect first"
fi

# ============================================================
# LOG & BLOCK
# ============================================================

if [ "$BLOCKED" = true ]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  mkdir -p "$(dirname "$LOG_FILE")"
  
  # Log the blocked attempt
  echo "[$TIMESTAMP] BLOCKED | project=$PROJECT_PATH | reason=$REASON | command=$COMMAND" >> "$LOG_FILE"
  
  # Output JSON telling Claude to stop
  printf '{"continue":false,"reason":"🛡️ Bash Guard: %s\n\nCommand blocked: %s\n\nIf you believe this is a false positive, review the command and use a safer alternative."}\n' "$REASON" "$COMMAND"
  exit 0
fi

# Command is safe — allow
echo '{"continue": true}'
