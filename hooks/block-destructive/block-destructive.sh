#!/usr/bin/env bash
# PreToolUse hook for Claude Code — blocks destructive bash commands
# Claude Code hook protocol: stdin = JSON, stdout = JSON with hookSpecificOutput
set -euo pipefail

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
mkdir -p "$LOG_DIR"

# Check for jq (required by Claude Code hook protocol)
if ! command -v jq &>/dev/null; then
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"jq is required but not installed"}}'
    exit 0
fi

# Read tool input JSON from stdin (Claude Code hook protocol)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
PROJECT_DIR=$(echo "$INPUT" | jq -r '.session_id // .cwd // ""')

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# Normalize for matching (collapse whitespace)
NORM_CMD=$(echo "$COMMAND" | tr -s '[:space:]' ' ')

# ─── Patterns and reasons ──────────────────────────
declare -A PATTERNS=(
    # rm variations: catch rm -rf, rm -r -f, rm -fr, rm --recursive --force
    ["rm\\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\\b"]="Recursive force delete (rm -rf variant)"
    ["rm\\s+--recursive\\s+--force"]="Recursive force delete (rm --recursive --force)"
    ["rm\\s+--no-preserve-root"]="rm --no-preserve-root (dangerous)"
    # SQL destruction
    ["DROP\\s+TABLE"]="SQL DROP TABLE"
    ["TRUNCATE\\s+(TABLE\\s+)?[a-zA-Z_"]="SQL TRUNCATE"
    # Git force push
    ["git\\s+push\\s+--force"]="Git force push (--force)"
    ["git\\s+push\\s+-f\\b"]="Git force push (-f)"
    # Chmod dangerous
    ["chmod\\s+777\\s+/"]="World-writable chmod 777 on root path"
    # Fork bomb
    [":\\(\\)\\s*\\{\\s*:"]="Fork bomb pattern detected"
)

# ─── Check patterns ─────────────────────────────────
for pattern in "${!PATTERNS[@]}"; do
    if echo "$NORM_CMD" | grep -qiE "$pattern"; then
        reason="${PATTERNS[$pattern]}"
        TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
        echo "[$TS] BLOCKED | reason=$reason | command=$COMMAND | project=$PROJECT_DIR" >> "$LOG_FILE"
        jq -n --arg reason "$reason" --arg cmd "$COMMAND" '{
            hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "deny",
                permissionDecisionReason: "\($reason). Command: \($cmd)"
            }
        }'
        exit 0  # exit 0 = deny (Claude Code convention)
    fi
done

# ─── Special: DELETE FROM without WHERE ────────────
if echo "$NORM_CMD" | grep -qiE 'DELETE\s+FROM' && \
   ! echo "$NORM_CMD" | grep -qiE 'DELETE\s+FROM.*\bWHERE\b'; then
    reason="SQL DELETE FROM without WHERE clause"
    TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    echo "[$TS] BLOCKED | reason=$reason | command=$COMMAND | project=$PROJECT_DIR" >> "$LOG_FILE"
    jq -n --arg reason "$reason" --arg cmd "$COMMAND" '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: "\($reason). Command: \($cmd)"
        }
    }'
    exit 0
fi

# ─── All checks passed — allow ─────────────────────
exit 0
