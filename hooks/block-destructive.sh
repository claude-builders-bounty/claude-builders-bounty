#!/usr/bin/env bash
#
# Claude Code pre-tool-use hook: blocks destructive bash commands.
# Install: copy to ~/.claude/hooks/ and register in settings.json.

set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

input=$(cat)

tool_name=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

if [[ "$tool_name" != "Bash" && "$tool_name" != "bash" ]]; then
  exit 0
fi

command=$(echo "$input" | python3 -c "
import sys, json
data = json.load(sys.stdin)
params = data.get('tool_input', {})
print(params.get('command', ''))
" 2>/dev/null || echo "")

if [[ -z "$command" ]]; then
  exit 0
fi

project_path=$(echo "$input" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('project_path', ''))
" 2>/dev/null || echo "unknown")

blocked=""
reason=""

if echo "$command" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|(-[a-zA-Z]*f[a-zA-Z]*r))\b'; then
  blocked="rm -rf"
  reason="Recursive force deletion can destroy entire directory trees."
fi

if echo "$command" | grep -qiE '\bDROP\s+TABLE\b'; then
  blocked="DROP TABLE"
  reason="Dropping database tables is irreversible data loss."
fi

if echo "$command" | grep -qE 'git\s+push\s+.*--force\b'; then
  blocked="git push --force"
  reason="Force-pushing rewrites remote history and can destroy teammates' work."
fi

if echo "$command" | grep -qiE '\bTRUNCATE\b'; then
  blocked="TRUNCATE"
  reason="Truncating a table removes all rows without logging individual deletions."
fi

if echo "$command" | grep -qiP '\bDELETE\s+FROM\b(?!.*\bWHERE\b)'; then
  blocked="DELETE FROM (no WHERE)"
  reason="DELETE FROM without a WHERE clause deletes every row in the table."
fi

if [[ -n "$blocked" ]]; then
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "[$timestamp] BLOCKED ($blocked) | project=$project_path | command=$command" >> "$LOG_FILE"

  cat <<EOF
BLOCKED: This command was rejected by the safety hook.

Pattern matched: $blocked
Reason: $reason

Attempted command:
  $command

The blocked attempt has been logged. Please use a safer alternative.
EOF
  exit 2
fi

exit 0
