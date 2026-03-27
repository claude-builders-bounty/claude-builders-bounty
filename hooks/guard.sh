#!/usr/bin/env bash
set -uo pipefail

if ! command -v jq &>/dev/null; then
	echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"guard.sh requires jq but it is not installed"}}'
	exit 0
fi

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty') || exit 0
PROJECT_PATH=$(echo "$INPUT" | jq -r '.cwd // empty') || true

[ -z "$COMMAND" ] && exit 0

REASON=""

# Split command on shell operators to get individual segments.
# Only check patterns in command position (not inside strings/arguments).
SEGMENTS=$(echo "$COMMAND" | sed 's/[;&|]\{1,2\}/\n/g; s/\$(/\n/g')

if echo "$SEGMENTS" | grep -qE '^[[:space:]]*rm[[:space:]]' && \
   echo "$SEGMENTS" | grep -qE '(-[a-zA-Z]*r|--recursive)' && \
   echo "$SEGMENTS" | grep -qE '(-[a-zA-Z]*f|--force)'; then
	REASON="rm -rf: recursive force delete"
elif echo "$SEGMENTS" | grep -qEi '^[[:space:]]*(DROP[[:space:]]+TABLE|(psql|mysql|sqlite3)[[:space:]].*DROP[[:space:]]+TABLE)'; then
	REASON="DROP TABLE: destructive database operation"
elif echo "$SEGMENTS" | grep -qEi '^[[:space:]]*(TRUNCATE|(psql|mysql|sqlite3)[[:space:]].*TRUNCATE)'; then
	REASON="TRUNCATE: destructive database operation"
elif echo "$SEGMENTS" | grep -qEi '^[[:space:]]*(DELETE[[:space:]]+FROM|(psql|mysql|sqlite3)[[:space:]].*DELETE[[:space:]]+FROM)' && \
     ! echo "$SEGMENTS" | grep -qEi 'DELETE[[:space:]]+FROM.*WHERE'; then
	REASON="DELETE FROM without WHERE clause"
elif echo "$SEGMENTS" | grep -qE '^[[:space:]]*git[[:space:]]+push[[:space:]]' && \
     echo "$COMMAND" | grep -qE -- '--force([[:space:]]|$)' && \
     ! echo "$COMMAND" | grep -qF 'force-with-lease'; then
	REASON="git push --force: destructive git operation"
elif echo "$SEGMENTS" | grep -qE '^[[:space:]]*git[[:space:]]+push[[:space:]]' && \
     echo "$COMMAND" | grep -qE -- '[[:space:]]-[a-zA-Z]*f([[:space:]]|$)'; then
	REASON="git push -f: destructive git operation"
fi

if [ -n "$REASON" ]; then
	LOG_DIR="$HOME/.claude/hooks"
	mkdir -p "$LOG_DIR"
	SAFE_CMD=$(echo "$COMMAND" | tr '\n' ' ')
	printf '[%s] BLOCKED | %s | cmd: %s | project: %s\n' \
		"$(date -Iseconds)" "$REASON" "$SAFE_CMD" "$PROJECT_PATH" \
		>> "$LOG_DIR/blocked.log"

	jq -n --arg reason "$REASON" '{
		hookSpecificOutput: {
			hookEventName: "PreToolUse",
			permissionDecision: "deny",
			permissionDecisionReason: $reason
		}
	}'
fi

exit 0
