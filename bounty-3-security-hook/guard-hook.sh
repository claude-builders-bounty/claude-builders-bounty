#!/usr/bin/env bash
# guard-hook.sh — Claude Code PreToolUse security hook
# Blocks destructive bash commands before execution.
#
# Receives JSON on stdin from Claude Code with the tool input.
# Exit 0 = allow, Exit 2 = block (stderr shown to Claude as reason).
#
# Blocked patterns:
#   - rm -rf / rm --recursive --force  (recursive forced deletion)
#   - DROP TABLE                        (SQL table destruction)
#   - git push --force / git push -f   (history rewrite)
#   - TRUNCATE                          (SQL table truncation)
#   - DELETE FROM without WHERE         (unconditional row deletion)

set -euo pipefail

LOGFILE="${HOME}/.claude/hooks/blocked.log"

# Read full JSON from stdin
INPUT="$(cat)"

# Extract the command field from tool_input.
# Uses jq if available, falls back to lightweight parsing.
if command -v jq &>/dev/null; then
    COMMAND="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')"
    PROJECT_DIR="$(printf '%s' "$INPUT" | jq -r '.cwd // "unknown"')"
else
    # Fallback: extract with grep/sed (handles simple JSON)
    COMMAND="$(printf '%s' "$INPUT" | grep -oP '"command"\s*:\s*"\K[^"]*' | head -1)" || true
    PROJECT_DIR="$(printf '%s' "$INPUT" | grep -oP '"cwd"\s*:\s*"\K[^"]*' | head -1)" || true
    [ -z "$PROJECT_DIR" ] && PROJECT_DIR="unknown"
fi

# If no command was extracted, allow (not a Bash tool call or empty command)
if [ -z "$COMMAND" ]; then
    exit 0
fi

# ── Logging function ─────────────────────────────────────────────────
log_blocked() {
    local label="$1"
    local timestamp
    timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

    # Ensure log directory exists
    mkdir -p "$(dirname "$LOGFILE")"

    # Escape double quotes and newlines in command for valid JSON
    local escaped_cmd
    escaped_cmd="$(printf '%s' "$COMMAND" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')"

    # Append structured log entry (one JSON object per line for easy parsing)
    printf '{"timestamp":"%s","rule":"%s","command":"%s","project":"%s"}\n' \
        "$timestamp" \
        "$label" \
        "$escaped_cmd" \
        "$PROJECT_DIR" \
        >> "$LOGFILE"
}

# ── Pattern checks ───────────────────────────────────────────────────

# 1. rm -rf (recursive forced deletion)
#    Matches: rm -rf, rm -fr, rm -r -f, rm -f -r, rm --recursive --force
RM_RF_PATTERN='rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+-[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*\s+-[a-zA-Z]*r[a-zA-Z]*|-[a-zA-Z]*rf[a-zA-Z]*|-[a-zA-Z]*fr[a-zA-Z]*)|rm\s+--recursive\s+--force|rm\s+--force\s+--recursive'
if printf '%s' "$COMMAND" | grep -qiE "$RM_RF_PATTERN"; then
    log_blocked "BLOCKED_RM_RF"
    printf 'BLOCKED: "rm -rf" (recursive forced deletion) destroys files irreversibly. Use targeted "rm" on specific files, or move files to trash instead.\n' >&2
    exit 2
fi

# 2. DROP TABLE (SQL table destruction)
DROP_TABLE_PATTERN='DROP\s+TABLE'
if printf '%s' "$COMMAND" | grep -qiE "$DROP_TABLE_PATTERN"; then
    log_blocked "BLOCKED_DROP_TABLE"
    printf 'BLOCKED: "DROP TABLE" permanently destroys database tables and all their data. Use a migration tool or create a backup first.\n' >&2
    exit 2
fi

# 3. git push --force (history rewrite)
#    Matches: git push --force, git push -f, git push origin main --force
#    Allows:  git push --force-with-lease (safe alternative)
GIT_FORCE_PATTERN='git\s+push\s+.*--force|git\s+push\s+.*\s+-f(\s|$)|git\s+push\s+-[a-zA-Z]*f'
GIT_FORCE_SAFE='--force-with-lease|--force-if-includes'
if printf '%s' "$COMMAND" | grep -qiE "$GIT_FORCE_PATTERN"; then
    if ! printf '%s' "$COMMAND" | grep -qiE -e "$GIT_FORCE_SAFE"; then
        log_blocked "BLOCKED_GIT_PUSH_FORCE"
        printf 'BLOCKED: "git push --force" rewrites remote history and can destroy teammates'\'' work. Use "git push --force-with-lease" for a safer alternative.\n' >&2
        exit 2
    fi
fi

# 4. TRUNCATE (SQL table truncation)
TRUNCATE_PATTERN='TRUNCATE\s+(TABLE\s+)?[a-zA-Z_]'
if printf '%s' "$COMMAND" | grep -qiE "$TRUNCATE_PATTERN"; then
    log_blocked "BLOCKED_TRUNCATE"
    printf 'BLOCKED: "TRUNCATE" removes all rows from a table instantly without transaction logging. Use DELETE with a WHERE clause or create a backup first.\n' >&2
    exit 2
fi

# 5. DELETE FROM without WHERE (unconditional row deletion)
#    Allows: DELETE FROM users WHERE id = 5
#    Blocks: DELETE FROM users; / DELETE FROM users
DELETE_PATTERN='DELETE\s+FROM\s+[a-zA-Z_"`\['"'"'.]+'
WHERE_PATTERN='WHERE\s+'
if printf '%s' "$COMMAND" | grep -qiE "$DELETE_PATTERN"; then
    if ! printf '%s' "$COMMAND" | grep -qiE "$WHERE_PATTERN"; then
        log_blocked "BLOCKED_DELETE_NO_WHERE"
        printf 'BLOCKED: "DELETE FROM" without a WHERE clause deletes every row in the table. Add a WHERE clause to target specific rows.\n' >&2
        exit 2
    fi
fi

# ── All checks passed — allow execution ──────────────────────────────
exit 0
