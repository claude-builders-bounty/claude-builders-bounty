#!/usr/bin/env bash
# pre-tool-use hook: blocks destructive bash commands in Claude Code
# Install: cp block-destructive.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x
#
# This hook reads the tool input from stdin (JSON), checks for dangerous
# patterns, and exits non-zero with a message to block execution.

set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

# Read the tool input JSON from stdin
INPUT=$(cat)

# Extract the command field from the JSON input
# Claude Code sends: {"tool_name":"Bash","tool_input":{"command":"..."}}
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    cmd = data.get('tool_input', {}).get('command', '')
    print(cmd)
except:
    print('')
" 2>/dev/null || true)

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Normalise for matching
LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

BLOCKED=0
REASON=""

# Pattern: rm -rf
if echo "$LOWER" | grep -qE 'rm\s+(-[a-z]*f[a-z]*\s+|-rf\s+|-fr\s+)--?[a-z].*'; then
  BLOCKED=1
  REASON="Blocked: 'rm -rf' detected. This can irreversibly delete files. Use targeted rm commands instead."
fi

# Pattern: git push --force / git push -f
if echo "$LOWER" | grep -qE 'git\s+push\s+.*(--force|-f)\b'; then
  BLOCKED=1
  REASON="Blocked: 'git push --force' detected. Force pushing rewrites shared history. Use --force-with-lease if absolutely necessary."
fi

# Pattern: DROP TABLE
if echo "$LOWER" | grep -qE 'drop\s+table\b'; then
  BLOCKED=1
  REASON="Blocked: 'DROP TABLE' detected. This permanently destroys database tables. Use migrations instead."
fi

# Pattern: TRUNCATE
if echo "$LOWER" | grep -qE '\btruncate\b'; then
  BLOCKED=1
  REASON="Blocked: 'TRUNCATE' detected. This deletes all rows in a table without a WHERE clause."
fi

# Pattern: DELETE FROM without WHERE
if echo "$LOWER" | grep -qE 'delete\s+from\b'; then
  if ! echo "$LOWER" | grep -qE '\bwhere\b'; then
    BLOCKED=1
    REASON="Blocked: 'DELETE FROM' without a WHERE clause detected. This deletes all rows."
  fi
fi

if [ "$BLOCKED" -eq 1 ]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT_PATH="$(pwd 2>/dev/null || echo 'unknown')"
  echo "${TIMESTAMP} | command: ${COMMAND} | project: ${PROJECT_PATH}" >> "$LOG_FILE"
  echo "$REASON" >&2
  exit 1
fi

exit 0
