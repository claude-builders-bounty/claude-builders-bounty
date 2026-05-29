#!/usr/bin/env bash
# Pre-tool-use hook for Claude Code
# Blocks destructive bash commands before they are executed
# Install: cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh

set -euo pipefail

# Configuration
LOG_FILE="${HOME}/.claude/hooks/blocked.log"

# Get the command from either argument or stdin
if [ $# -gt 0 ]; then
    TOOL_INPUT="$*"
else
    TOOL_INPUT="$(cat)"
fi

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log blocked attempts
log_blocked() {
    local command="$1"
    local reason="$2"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local project_path
    project_path="$(pwd)"
    
    echo "[$timestamp] BLOCKED: $command | Reason: $reason | Project: $project_path" >> "$LOG_FILE"
}

# Function to check if command contains dangerous patterns
check_command() {
    local cmd="$1"
    
    # Pattern 1: rm -rf (recursive force delete)
    if echo "$cmd" | grep -qiE 'rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\s'; then
        log_blocked "$cmd" "rm -rf: Recursive force deletion blocked"
        echo "BLOCKED: This command contains 'rm -rf' which performs recursive force deletion. This is destructive and cannot be undone. Please use a safer alternative or ask the user to confirm manually."
        exit 1
    fi
    
    # Pattern 2: DROP TABLE
    if echo "$cmd" | grep -qiE 'DROP\s+TABLE'; then
        log_blocked "$cmd" "DROP TABLE: Database table deletion blocked"
        echo "BLOCKED: This command contains 'DROP TABLE' which permanently deletes database tables. This is destructive and cannot be undone. Please use a safer alternative or ask the user to confirm manually."
        exit 1
    fi
    
    # Pattern 3: git push --force
    if echo "$cmd" | grep -qiE 'git\s+push\s+.*--force'; then
        log_blocked "$cmd" "git push --force: Force push blocked"
        echo "BLOCKED: This command contains 'git push --force' which overwrites remote history. This can cause data loss for other collaborators. Please use 'git push --force-with-lease' instead or ask the user to confirm manually."
        exit 1
    fi
    
    # Pattern 4: TRUNCATE
    if echo "$cmd" | grep -qiE 'TRUNCATE\s+TABLE'; then
        log_blocked "$cmd" "TRUNCATE TABLE: Database truncation blocked"
        echo "BLOCKED: This command contains 'TRUNCATE TABLE' which removes all rows from a table. This is destructive and cannot be undone. Please use a safer alternative or ask the user to confirm manually."
        exit 1
    fi
    
    # Pattern 5: DELETE FROM without WHERE clause
    if echo "$cmd" | grep -qiE 'DELETE\s+FROM' && ! echo "$cmd" | grep -qiE 'WHERE'; then
        log_blocked "$cmd" "DELETE FROM without WHERE: Unconditional deletion blocked"
        echo "BLOCKED: This command contains 'DELETE FROM' without a 'WHERE' clause, which deletes all rows from the table. Please add a WHERE clause to limit the deletion or ask the user to confirm manually."
        exit 1
    fi
    
    # Pattern 6: mkfs (format filesystem)
    if echo "$cmd" | grep -qiE 'mkfs\.'; then
        log_blocked "$cmd" "mkfs: Filesystem formatting blocked"
        echo "BLOCKED: This command contains 'mkfs' which formats a filesystem, erasing all data. This is destructive and cannot be undone. Please ask the user to confirm manually."
        exit 1
    fi
    
    # Pattern 7: dd with of= (disk write)
    if echo "$cmd" | grep -qiE 'dd\s+.*of='; then
        log_blocked "$cmd" "dd with of=: Direct disk write blocked"
        echo "BLOCKED: This command uses 'dd' with 'of=' which performs direct disk writes. This can overwrite data irreversibly. Please ask the user to confirm manually."
        exit 1
    fi
    
    # Pattern 8: chmod 777 (overly permissive)
    if echo "$cmd" | grep -qiE 'chmod\s+777'; then
        log_blocked "$cmd" "chmod 777: Overly permissive permissions blocked"
        echo "BLOCKED: This command uses 'chmod 777' which gives everyone full permissions. This is a security risk. Please use more restrictive permissions like 'chmod 755' for directories or 'chmod 644' for files."
        exit 1
    fi
}

# Main execution
if [ -z "$TOOL_INPUT" ]; then
    # No input provided, allow the command
    exit 0
fi

# Check the command
check_command "$TOOL_INPUT"

# If we get here, the command is safe
exit 0
