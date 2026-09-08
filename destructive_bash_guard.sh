#!/usr/bin/env bash

set -u

HOOK_DIR="${HOME}/.claude/hooks"
LOG_FILE="${HOOK_DIR}/blocked.log"

mkdir -p "$HOOK_DIR"

INPUT="$(cat)"

COMMAND="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')"
PROJECT_PATH="$(printf '%s' "$INPUT" | jq -r '.cwd // empty')"
TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // "Bash"')"

[ "$TOOL_NAME" != "Bash" ] && exit 0
[ -z "$COMMAND" ] && exit 0
[ -z "$PROJECT_PATH" ] && PROJECT_PATH="$(pwd)"

REASON=""

# Block rm when both recursive and force flags are present.
if printf '%s\n' "$COMMAND" |
    grep -Eiq '(^|[;&|[:space:]])rm([[:space:]]+-[^[:space:]]*)*[[:space:]]+.*'; then

    RM_ARGS="$(printf '%s\n' "$COMMAND" |
        sed -E 's/.*(^|[;&|[:space:]])rm[[:space:]]+//')"

    HAS_RECURSIVE=0
    HAS_FORCE=0

    printf '%s\n' "$RM_ARGS" |
        grep -Eiq '(^|[[:space:]])-[^[:space:]]*r[^[:space:]]*([[:space:]]|$)|--recursive' &&
        HAS_RECURSIVE=1

    printf '%s\n' "$RM_ARGS" |
        grep -Eiq '(^|[[:space:]])-[^[:space:]]*f[^[:space:]]*([[:space:]]|$)|--force' &&
        HAS_FORCE=1

    if [ "$HAS_RECURSIVE" -eq 1 ] && [ "$HAS_FORCE" -eq 1 ]; then
        REASON="Blocked: rm uses both recursive and force flags and can permanently delete directory trees."
    fi
fi

# Block git push --force / -f, but allow --force-with-lease.
if [ -z "$REASON" ] &&
   printf '%s\n' "$COMMAND" |
   grep -Eiq '(^|[;&|[:space:]])git[[:space:]]+push([^;&|]*)[[:space:]](--force|-f)([[:space:]]|$)'; then
    REASON="Blocked: git push --force can rewrite remote history and discard commits."
fi

# Block DROP TABLE.
if [ -z "$REASON" ] &&
   printf '%s\n' "$COMMAND" |
   grep -Eiq 'DROP[[:space:]]+TABLE'; then
    REASON="Blocked: DROP TABLE permanently removes a database table and its data."
fi

# Block TRUNCATE / TRUNCATE TABLE.
if [ -z "$REASON" ] &&
   printf '%s\n' "$COMMAND" |
   grep -Eiq 'TRUNCATE([[:space:]]+TABLE)?'; then
    REASON="Blocked: TRUNCATE permanently removes all rows from a table."
fi

# Block DELETE FROM statements that do not contain WHERE.
if [ -z "$REASON" ] &&
   printf '%s\n' "$COMMAND" |
   grep -Eiq 'DELETE[[:space:]]+FROM'; then

    OLDIFS="$IFS"
    IFS=';'
    HAS_UNSAFE_DELETE=0

    # Split chained SQL statements so a WHERE in another statement
    # cannot make an unsafe DELETE look safe.
    read -ra STATEMENTS <<< "$COMMAND"
    IFS="$OLDIFS"

    for STATEMENT in "${STATEMENTS[@]}"; do
        if printf '%s\n' "$STATEMENT" |
            grep -Eiq 'DELETE[[:space:]]+FROM'; then

            if ! printf '%s\n' "$STATEMENT" |
                grep -Eiq 'WHERE'; then
                HAS_UNSAFE_DELETE=1
                break
            fi
        fi
    done

    if [ "$HAS_UNSAFE_DELETE" -eq 1 ]; then
        REASON="Blocked: DELETE FROM without WHERE can remove every row from a table."
    fi
fi

[ -z "$REASON" ] && exit 0

TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

printf '%s\tproject=%s\tcommand=%s\treason=%s\n' \
    "$TIMESTAMP" \
    "$PROJECT_PATH" \
    "$COMMAND" \
    "$REASON" >> "$LOG_FILE"

jq -n \
    --arg reason "$REASON" \
    '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: $reason
        }
    }'

exit 0
