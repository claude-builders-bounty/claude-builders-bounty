#!/bin/bash
# Pre-tool-use hook: Block destructive bash commands
# Installs to: ~/.claude/hooks/pre-tool-use.sh
# Logs to: ~/.claude/hooks/blocked.log

HOOKS_DIR="$HOME/.claude/hooks"
LOG_FILE="$HOOKS_DIR/blocked.log"
PROJECT_PATH="$(pwd)"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Ensure log directory exists
mkdir -p "$HOOKS_DIR"

# Function to log blocked attempts
log_blocked() {
    local pattern="$1"
    local reason="$2"
    echo "$TIMESTAMP | $COMMAND | $pattern | $PROJECT_PATH" >> "$LOG_FILE"
    echo "BLOCKED: Command matches destructive pattern '$pattern'"
    echo "Reason: $reason"
    echo "Logged to: $LOG_FILE"
    exit 1
}

# Function to check SQL dangerous patterns
check_sql() {
    local cmd="$1"
    
    # DROP TABLE
    if echo "$cmd" | grep -qiE 'DROP\s+TABLE'; then
        log_blocked "DROP TABLE" "SQL table destruction"
    fi
    
    # TRUNCATE
    if echo "$cmd" | grep -qiE 'TRUNCATE\s+TABLE?\s*\w+'; then
        log_blocked "TRUNCATE" "SQL data removal"
    fi
    
    # DELETE FROM without WHERE
    if echo "$cmd" | grep -qiE 'DELETE\s+FROM' && ! echo "$cmd" | grep -qiE 'WHERE'; then
        log_blocked "DELETE FROM (no WHERE)" "SQL mass deletion without WHERE clause"
    fi
}

# Function to check Git dangerous patterns
check_git() {
    local cmd="$1"
    
    # git push --force
    if echo "$cmd" | grep -qiE 'git\s+push.*--force'; then
        log_blocked "git push --force" "Destructive force push"
    fi
    
    # git push -f
    if echo "$cmd" | grep -qiE 'git\s+push.*-f'; then
        log_blocked "git push -f" "Destructive force push shorthand"
    fi
}

# Function to check filesystem dangerous patterns
check_filesystem() {
    local cmd="$1"
    
    # rm -rf
    if echo "$cmd" | grep -qiE 'rm\s+.*-rf'; then
        log_blocked "rm -rf" "Recursive forced deletion"
    fi
    
    # rm -rf /
    if echo "$cmd" | grep -qiE 'rm\s+(-[a-z]*rf|--recursive|--force).*\s+/\s*$'; then
        log_blocked "rm -rf /" "Root filesystem destruction"
    fi
}

# Main execution
# This script receives the tool call via stdin (Claude Code hooks format)
# For now, we check the command passed as argument

COMMAND="${1:-$(cat)}"

# Skip if no command
if [ -z "$COMMAND" ]; then
    exit 0
fi

# Run all checks
check_filesystem "$COMMAND"
check_sql "$COMMAND"
check_git "$COMMAND"

# If we reach here, command is allowed
exit 0