#!/bin/bash
# block-destructive.sh -- Claude Code pre-tool-use hook
# Blocks dangerous bash commands before execution
# Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

set -euo pipefail

CONFIG_DIR="${CLAUDE_HOOKS_DIR:-$HOME/.claude/hooks}"
LOG_FILE="${CONFIG_DIR}/blocked.log"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        *) ARGS+=("$1"); shift ;;
    esac
done

CMD="${ARGS[*]}"

# Patterns that BLOCK (high risk)
BLOCKED_PATTERNS=(
    'DROP\s+TABLE'
    'DROP\s+DATABASE'
    'TRUNCATE\s+'
    'git\s+push\s+--force\s'
    'git\s+commit\s+--amend\s+--no-edit'
    'git\s+reset\s+--hard'
    'mkfs\.'
    ':(){ :|:& };:'
    'wget\s+.*\||curl\s+.*\|.*bash'
    'sudo\s+rm\s+-rf\s'
    'eval\s+\$\('
    'chmod\s+-R\s+0\s+\/'
)

# Patterns that WARN (medium risk)
WARN_PATTERNS=(
    'git\s+push\s+--force-with-lease'
    'ALTER\s+TABLE'
    'UPDATE\s+\w+\s+SET'
    'DELETE\s+FROM'
)

check_pattern() {
    echo "$1" | grep -qiE "$2" 2>/dev/null && return 0 || return 1
}

log_msg() {
    local level="$1" reason="$2"
    local ts; ts=$(date '+%Y-%m-%d %H:%M:%S')
    local cwd; cwd=$(pwd 2>/dev/null || echo "?")
    echo "[${level}] ${ts} | cwd: ${cwd} | reason: ${reason} | cmd: ${CMD}" >> "$LOG_FILE"
}

# Check blocked patterns
for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if check_pattern "$CMD" "$pattern"; then
        if $DRY_RUN; then
            echo "[DRY-RUN] Would block: ${CMD} (matched: ${pattern})"
            log_msg "WARN" "DRY-RUN would block '${pattern}'"
            exit 0
        fi
        echo "[BLOCKED] Command blocked: ${pattern}"
        log_msg "BLOCKED" "matched pattern '${pattern}'"
        exit 1
    fi
done

# Check warn patterns
for pattern in "${WARN_PATTERNS[@]}"; do
    if check_pattern "$CMD" "$pattern"; then
        echo "[WARN] Destructive command: ${CMD} (matched: ${pattern})"
        log_msg "WARN" "matched warning pattern '${pattern}'"
    fi
done

exit 0
