#!/usr/bin/env bash
# pre-tool-use hook: blocks destructive bash commands
# Place at ~/.claude/hooks/pre-tool-use.sh
# Configure in Claude Code settings to run before tool execution

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read the tool input from stdin (JSON passed by Claude Code)
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check bash commands
if [ "$TOOL_NAME" != "Bash" ] || [ -z "$COMMAND" ]; then
  exit 0
fi

# Normalize command for pattern matching
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Destructive patterns to block
# Each pattern: regex|description
PATTERNS=(
  'rm[[:space:]]+(-[a-z]*r[a-z]*f[a-z]*|--recursive)[[:space:]]+|rm -rf: recursively deletes files/directories'
  'rm[[:space:]]+(-[a-z]*f[a-z]*r[a-z]*|--recursive)[[:space:]]+|rm -rf: recursively deletes files/directories'
  'drop[[:space:]]+table|DROP TABLE: destroys database tables'
  'drop[[:space:]]+database|DROP DATABASE: destroys entire databases'
  'truncate[[:space:]]+|TRUNCATE: empties tables without logging'
  'delete[[:space:]]+from[[:space:]]+[^;]*(;|$)|DELETE FROM without WHERE: deletes all rows'
  'git[[:space:]]+push[[:space:]]+.*--force|git push --force: overwrites remote history'
  'git[[:space:]]+push[[:space:]]+.*-f[[:space:]]|git push -f: overwrites remote history'
  'git[[:space:]]+reset[[:space:]]+--hard|git reset --hard: discards all uncommitted changes'
  'git[[:space:]]+clean[[:space:]]+-[a-z]*d[a-z]*f|git clean -df: removes untracked files/dirs'
  'chmod[[:space:]]+-R[[:space:]]+777|chmod -R 777: makes everything world-writable'
  'chown[[:space:]]+-R[[:space:]]+|chown -R: recursively changes ownership'
  'mkfs|mkfs: formats a filesystem'
  'dd[[:space:]]+.*of=/dev/|dd to device: writes directly to disk device'
  '>[[:space:]]*/dev/sd|redirect to disk device: overwrites raw disk'
  ':(){.*};:|fork bomb: denial of service'
  'shutdown|shutdown: powers off the machine'
  'reboot|reboot: restarts the machine'
  'halt|halt: stops the machine'
  'killall|killall: kills all processes by name'
  'pkill[[:space:]]+-9|pkill -9: force-kills processes'
)

check_pattern() {
  local cmd="$1"
  local pattern_desc="$2"
  local pattern="${pattern_desc%%|*}"
  local description="${pattern_desc#*|}"

  if echo "$cmd" | grep -qE "$pattern" 2>/dev/null; then
    # Log the blocked attempt
    echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"command\":\"$(echo "$cmd" | sed 's/"/\\"/g')\",\"reason\":\"$description\",\"project_path\":\"$(pwd | sed 's/"/\\"/g')\"}" >> "$LOG_FILE"

    # Output JSON response telling Claude why the command was blocked
    cat <<EOF
{
  "decision": "block",
  "reason": "Command blocked by pre-tool-use hook: $description. This destructive operation was intercepted to prevent data loss. If this is intentional, ask the user to run the command manually."
}
EOF
    exit 0
  fi
}

# Check DELETE FROM without WHERE separately (more complex)
check_delete_without_where() {
  local cmd="$CMD_LOWER"
  # Match DELETE FROM ... ; with no WHERE between FROM and ; or end
  if echo "$cmd" | grep -qE 'delete[[:space:]]+from[[:space:]]+' 2>/dev/null; then
    if ! echo "$cmd" | grep -qE 'where[[:space:]]+' 2>/dev/null; then
      echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"command\":\"$(echo "$COMMAND" | sed 's/"/\\"/g')\",\"reason\":\"DELETE FROM without WHERE clause\",\"project_path\":\"$(pwd | sed 's/"/\\"/g')\"}" >> "$LOG_FILE"
      cat <<EOF
{
  "decision": "block",
  "reason": "Command blocked by pre-tool-use hook: DELETE FROM without WHERE clause. This would delete all rows in the table. If intentional, add a WHERE clause or ask the user to run it manually."
}
EOF
      exit 0
    fi
  fi
}

# Run all checks
for pd in "${PATTERNS[@]}"; do
  check_pattern "$CMD_LOWER" "$pd"
done

check_delete_without_where

# Command is safe — allow execution
exit 0
