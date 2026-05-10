#!/bin/bash
# dangerous-bash-guard.sh — Claude Code PreToolUse hook that blocks dangerous bash commands.
#
# This is the bash version for systems without Python. For the full-featured
# version with logging and all pattern support, use dangerous_bash_guard.py instead.
#
# Exit codes:
#   0 + no output = allow
#   0 + JSON output = deny (with reason)

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract the tool name
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Only check Bash tool calls
if [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

# Extract the command
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
    exit 0
fi

# ── Pattern Checks ────────────────────────────────────────────────

# rm -rf
if echo "$COMMAND" | grep -qE 'rm\s+.*-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|rm\s+.*-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*'; then
    jq -n '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: "[dangerous-bash-guard] Blocked: Recursive force delete. Use targeted deletions instead."
        }
    }'
    # Log
    LOG_DIR="${CLAUDE_PROJECT_DIR:-$HOME}/.claude/hooks"
    mkdir -p "$LOG_DIR"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq -n --arg ts "$TIMESTAMP" --arg cmd "$COMMAND" --arg reason "rm -rf blocked" \
        '{timestamp: $ts, command: $cmd, reason: $reason}' >> "$LOG_DIR/blocked.log" 2>/dev/null || true
    exit 0
fi

# DROP TABLE / DROP DATABASE
if echo "$COMMAND" | grep -qiE 'DROP\s+(TABLE|DATABASE|SCHEMA)'; then
    jq -n '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: "[dangerous-bash-guard] Blocked: DROP TABLE/DATABASE is irreversible. Use migrations or soft deletes instead."
        }
    }'
    exit 0
fi

# git push --force / -f (but allow --force-with-lease)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force-with-lease'; then
    # --force-with-lease is safe, allow
    exit 0
fi
if echo "$COMMAND" | grep -qE 'git\s+push\s+[^|&;]*(--force\b|-f\b)'; then
    jq -n '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: "[dangerous-bash-guard] Blocked: Force push rewrites remote history. Use --force-with-lease or rebase instead."
        }
    }'
    exit 0
fi

# TRUNCATE
if echo "$COMMAND" | grep -qiE 'TRUNCATE\s+(TABLE\s+)?[a-zA-Z_"`]'; then
    jq -n '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: "[dangerous-bash-guard] Blocked: TRUNCATE removes all rows without logging. Use DELETE with WHERE instead."
        }
    }'
    exit 0
fi

# DELETE FROM without WHERE
if echo "$COMMAND" | grep -qiE 'DELETE\s+FROM'; then
    if ! echo "$COMMAND" | grep -qiE '\bWHERE\b'; then
        jq -n '{
            hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "deny",
                permissionDecisionReason: "[dangerous-bash-guard] Blocked: DELETE FROM without WHERE clause deletes all rows. Add a WHERE clause."
            }
        }'
        exit 0
    fi
fi

# No dangerous pattern found — allow
exit 0
