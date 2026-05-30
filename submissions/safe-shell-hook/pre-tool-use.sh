#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

INPUT=$(cat)

TOOL=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool', d.get('name', '')))
except:
    print('')
" 2>/dev/null || echo "")

if [[ "$TOOL" != "Bash" ]]; then
  echo "$INPUT"
  exit 0
fi

COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('input', d.get('arguments', {}).get('command', '')))
except:
    print('')
" 2>/dev/null || echo "")

CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

block() {
  local reason="$1"
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  local dir
  dir=$(pwd)

  echo "[$ts] BLOCKED | dir=$dir | cmd=$COMMAND | reason=$reason" >> "$LOG_FILE"

  python3 -c "
import json, sys
d = json.loads('''$INPUT''')
d['result'] = {
    'is_error': True,
    'message': '''⛔ SAFETY BLOCK: $reason

Claude attempted a blocked command.

Command: $COMMAND
Reason: $reason
Logged: $LOG_FILE'''
}
print(json.dumps(d))
"
  exit 0
}

if echo "$CMD_LOWER" | grep -qP 'rm\s+-rf\s+/\s*$'; then
  block "rm -rf / — would delete entire filesystem"
fi

if echo "$CMD_LOWER" | grep -qP 'rm\s+-rf\s+--no-preserve-root'; then
  block "rm -rf --no-preserve-root — bypasses safety, destroys system"
fi

if echo "$CMD_LOWER" | grep -qP '\bdrop\s+(table|database)\b'; then
  block "DROP TABLE/DATABASE — would destroy database data"
fi

if echo "$CMD_LOWER" | grep -qP '\btruncate\b'; then
  block "TRUNCATE — would wipe database table"
fi

if echo "$CMD_LOWER" | grep -qP 'git\s+push\s+--force'; then
  block "git push --force — would overwrite remote history"
fi

if echo "$CMD_LOWER" | grep -qP '\bdelete\s+from\b(?!.*\bwhere\b)'; then
  block "DELETE FROM without WHERE — would delete all rows"
fi

echo "$INPUT"
