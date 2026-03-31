#!/usr/bin/env bash
# =============================================================================
# pre-tool-use-safety-hook — Blocks destructive bash commands in Claude Code
#
# Claude Code pre-tool-use hook that intercepts dangerous commands before
# execution. Reads JSON from stdin, checks the command against 12+ destructive
# patterns, logs blocked attempts, and returns a deny decision.
#
# Hook format: https://docs.anthropic.com/en/docs/claude-code/hooks
# =============================================================================

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"

# ---------------------------------------------------------------------------
# Read JSON input from stdin
# Claude Code sends: {"tool_name":"Bash","tool_input":{"command":"..."},...}
# ---------------------------------------------------------------------------
INPUT="$(cat)"

TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')"

# Only inspect Bash tool calls — let everything else pass through
if [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

COMMAND="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')"
PROJECT_DIR="$(printf '%s' "$INPUT" | jq -r '.cwd // "unknown"')"

# ---------------------------------------------------------------------------
# Destructive pattern definitions
# Each entry: "PATTERN|DESCRIPTION"
# Patterns are checked case-insensitively against the full command string.
# ---------------------------------------------------------------------------
DANGEROUS_PATTERNS=(
    'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|Recursive force delete (rm -rf)'
    'rm\s+-[a-zA-Z]*f[a-zA-Z]*r|Recursive force delete (rm -fr)'
    'rm\s+-rf\b|Recursive force delete (rm -rf)'
    'DROP\s+TABLE|SQL DROP TABLE'
    'DROP\s+DATABASE|SQL DROP DATABASE'
    'TRUNCATE\s+TABLE|SQL TRUNCATE TABLE'
    'TRUNCATE\s|SQL TRUNCATE'
    'git\s+push\s+.*--force\b|Git force push (--force)'
    'git\s+push\s+.*-f\b|Git force push (-f)'
    'mkfs\.|Format filesystem (mkfs)'
    'dd\s+if=.*of=/dev/|Direct disk write (dd)'
    '>\s*/dev/sd|Overwrite block device'
    'chmod\s+-R\s+777\s+/|Recursive chmod 777 on root'
    'chown\s+-R\s+.*\s+/\s|Recursive chown on root'
)

# Special pattern: DELETE FROM without WHERE clause
DELETE_WITHOUT_WHERE='DELETE\s+FROM\s+\S+\s*;|DELETE\s+FROM\s+\S+\s*$'

# ---------------------------------------------------------------------------
# Check command against each dangerous pattern
# ---------------------------------------------------------------------------
for entry in "${DANGEROUS_PATTERNS[@]}"; do
    PATTERN="${entry%%|*}"
    DESCRIPTION="${entry##*|}"

    if printf '%s' "$COMMAND" | grep -iPq "$PATTERN"; then
        # Log the blocked attempt
        mkdir -p "$(dirname "$LOG_FILE")"
        printf '[%s] BLOCKED | pattern="%s" | project="%s" | command="%s"\n' \
            "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
            "$DESCRIPTION" \
            "$PROJECT_DIR" \
            "$COMMAND" >> "$LOG_FILE"

        # Return deny decision to Claude Code
        jq -n \
            --arg reason "BLOCKED: ${DESCRIPTION}. Command: ${COMMAND}" \
            '{
                hookSpecificOutput: {
                    hookEventName: "PreToolUse",
                    permissionDecision: "deny",
                    permissionDecisionReason: $reason
                }
            }'
        exit 0
    fi
done

# Check DELETE FROM without WHERE (special two-step check)
if printf '%s' "$COMMAND" | grep -iPq 'DELETE\s+FROM'; then
    if ! printf '%s' "$COMMAND" | grep -iPq 'DELETE\s+FROM\s+\S+\s+WHERE'; then
        DESCRIPTION="DELETE FROM without WHERE clause"

        mkdir -p "$(dirname "$LOG_FILE")"
        printf '[%s] BLOCKED | pattern="%s" | project="%s" | command="%s"\n' \
            "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
            "$DESCRIPTION" \
            "$PROJECT_DIR" \
            "$COMMAND" >> "$LOG_FILE"

        jq -n \
            --arg reason "BLOCKED: ${DESCRIPTION}. Command: ${COMMAND}" \
            '{
                hookSpecificOutput: {
                    hookEventName: "PreToolUse",
                    permissionDecision: "deny",
                    permissionDecisionReason: $reason
                }
            }'
        exit 0
    fi
fi

# ---------------------------------------------------------------------------
# Command is safe — allow it through (empty output = allow)
# ---------------------------------------------------------------------------
exit 0
