#!/bin/bash
# block-destructive.sh — Pre-tool-use hook for Claude Code
# Blocks dangerous bash commands and logs attempts.
# Usage: placed in ~/.claude/hooks/, configured in settings.json

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOGFILE="${HOME}/.claude/hooks/blocked.log"

# Patterns to block (case-insensitive grep)
PATTERNS=(
  'rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*[[:space:]]'  # rm -rf variants
  'rm[[:space:]]+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*[[:space:]]'  # rm -fr variants
  'DROP[[:space:]]+TABLE'
  'TRUNCATE[[:space:]]+TABLE'
  'git[[:space:]]+push[[:space:]]+.*--force'
  'git[[:space:]]+push[[:space:]]+.*-f[^a-zA-Z]'             # git push -f
  'DELETE[[:space:]]+FROM'                                     # DELETE FROM (any)
)

BLOCKED=0
REASON=""

for pattern in "${PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    BLOCKED=1
    case "$pattern" in
      *rm*)              REASON="Blocked: 'rm -rf' is destructive and irreversible. Use 'rm' without -rf, or be more specific about what to delete." ;;
      *DROP*)            REASON="Blocked: 'DROP TABLE' destroys database schema. This requires manual confirmation." ;;
      *TRUNCATE*)        REASON="Blocked: 'TRUNCATE TABLE' destroys all data in a table. This requires manual confirmation." ;;
      *push*--force*)    REASON="Blocked: 'git push --force' rewrites remote history. Use --force-with-lease instead, or push to a feature branch." ;;
      *push*-f*)         REASON="Blocked: 'git push -f' rewrites remote history. Use --force-with-lease instead." ;;
      *DELETE*)          REASON="Blocked: 'DELETE FROM' without WHERE clause can destroy all rows. Add a WHERE clause or confirm intent." ;;
    esac
    break
  fi
done

if [ "$BLOCKED" -eq 1 ]; then
  # Log the attempt
  mkdir -p "$(dirname "$LOGFILE")"
  echo "${TIMESTAMP} | ${CWD:-unknown} | ${COMMAND}" >> "$LOGFILE"

  # Return deny decision to Claude
  jq -n \
    --arg reason "$REASON" \
    --arg cmd "$COMMAND" \
    '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: ($reason + "\n\nAttempted command: " + $cmd)
      }
    }'
else
  exit 0  # No match — let normal permission flow handle it
fi
