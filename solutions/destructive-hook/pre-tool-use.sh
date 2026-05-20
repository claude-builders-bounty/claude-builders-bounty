#!/bin/bash
#
# Claude Code pre-tool-use Hook: Destructive Command Blocker
# 
# This hook intercepts and blocks dangerous bash commands before execution.
# It follows the Claude Code hooks specification for pre-tool-use hooks.
#
# Installation:
#   mkdir -p ~/.claude/hooks
#   cp pre-tool-use.sh ~/.claude/hooks/
#   chmod +x ~/.claude/hooks/pre-tool-use.sh
#
# Log location: ~/.claude/hooks/blocked.log
#

set -e

# Configuration
LOG_FILE="$HOME/.claude/hooks/blocked.log"
PROJECT_PATH="${PWD:-unknown}"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

# Function to log blocked attempts
log_blocked() {
    local command="$1"
    local pattern="$2"
    local reason="$3"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    cat >> "$LOG_FILE" << EOF
[$timestamp] BLOCKED: $command
  Pattern: $pattern
  Project: $PROJECT_PATH
  Reason: $reason

EOF
}

# Function to send blocking message to Claude
block_command() {
    local command="$1"
    local reason="$2"
    
    # Output JSON that Claude Code understands for blocking
    echo "BLOCK: $reason"
    echo "Command '$command' was blocked for safety."
    exit 2
}

# Function to allow command
allow_command() {
    exit 0
}

# Read stdin for tool use information
# Claude Code passes tool information via stdin in JSON format
INPUT=""
if [ -t 0 ]; then
    # Interactive mode - check arguments
    if [ -n "$1" ]; then
        INPUT="$1"
    else
        allow_command
    fi
else
    # Piped input
    INPUT=$(cat)
fi

# Parse the tool and command from input
TOOL=""
COMMAND=""

# Try to parse JSON input
if command -v jq &>/dev/null; then
    TOOL=$(echo "$INPUT" | jq -r '.tool // empty' 2>/dev/null || echo "")
    COMMAND=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null || echo "")
elif command -v python3 &>/dev/null; then
    TOOL=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool',''))" 2>/dev/null || echo "")
    COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null || echo "")
else
    # Fallback: simple grep parsing
    TOOL=$(echo "$INPUT" | grep -oP '"tool"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")
    COMMAND=$(echo "$INPUT" | grep -oP '"command"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")
fi

# If no tool specified, check if input looks like a command
if [ -z "$TOOL" ] && [ -n "$INPUT" ]; then
    # Assume it's a bash command check
    INPUT_START=$(echo "$INPUT" | cut -c1-10)
    if echo "$INPUT_START" | grep -qiE '^(rm|git|DROP|DELETE|TRUNCATE)'; then
        COMMAND="$INPUT"
        TOOL="bash"
    fi
fi

# Only check bash commands
if [ "$TOOL" != "bash" ] && [ -z "$COMMAND" ]; then
    allow_command
fi

# If we have a direct command argument, use it
if [ -n "$1" ]; then
    COMMAND="$*"
fi

# If no command to check, allow
if [ -z "$COMMAND" ]; then
    allow_command
fi

# Normalize command for checking
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

#
# Dangerous pattern checks
#

# 1. rm -rf with dangerous paths
if [[ "$CMD_LOWER" =~ rm\ -rf\ /[^[:space:]]* ]] || [[ "$CMD_LOWER" =~ rm\ -rf\ /$ ]]; then
    log_blocked "$COMMAND" "rm -rf with root path" "System destruction attempt"
    block_command "$COMMAND" "The 'rm -rf /' command or variants are blocked to prevent system destruction."
fi

if [[ "$CMD_LOWER" =~ rm\ -rf\ ~ ]] || [[ "$CMD_LOWER" =~ rm\ -rf\ \$home ]]; then
    log_blocked "$COMMAND" "rm -rf with home path" "Home directory destruction attempt"
    block_command "$COMMAND" "The 'rm -rf ~' command is blocked to prevent home directory destruction."
fi

if [[ "$CMD_LOWER" =~ rm\ -rf\ * ]] && [[ "$CMD_LOWER" =~ \*\ *$ || "$CMD_LOWER" =~ \*\/ ]]; then
    log_blocked "$COMMAND" "rm -rf with wildcard" "Potentially destructive wildcard deletion"
    block_command "$COMMAND" "The 'rm -rf' command with wildcards is blocked to prevent accidental data loss."
fi

# 2. SQL destructive commands
if [[ "$CMD_LOWER" =~ drop\ table ]] || [[ "$CMD_LOWER" =~ drop\ database ]]; then
    log_blocked "$COMMAND" "SQL DROP" "SQL data destruction attempt"
    block_command "$COMMAND" "SQL DROP commands are blocked to prevent data loss. Use a dedicated SQL client with proper safeguards."
fi

if [[ "$CMD_LOWER" =~ truncate\ table ]] || [[ "$CMD_LOWER" =~ truncate\ table ]]; then
    log_blocked "$COMMAND" "SQL TRUNCATE" "SQL data truncation attempt"
    block_command "$COMMAND" "SQL TRUNCATE commands are blocked to prevent data loss."
fi

# 3. DELETE FROM without WHERE clause
if [[ "$CMD_LOWER" =~ delete\ from ]]; then
    if [[ ! "$CMD_LOWER" =~ where ]]; then
        log_blocked "$COMMAND" "DELETE without WHERE" "Unrestricted DELETE attempt"
        block_command "$COMMAND" "DELETE FROM without a WHERE clause is blocked to prevent accidental data deletion."
    fi
fi

# 4. Git force push
if [[ "$CMD_LOWER" =~ git\ push\ --force ]] || [[ "$CMD_LOWER" =~ git\ push\ -f ]] || [[ "$CMD_LOWER" =~ git\ push\ --force-with-lease ]]; then
    log_blocked "$COMMAND" "git push --force" "Force push attempt"
    block_command "$COMMAND" "Force pushing is blocked to prevent history destruction. Use regular 'git push' or rebase locally."
fi

# 5. Git hard reset with uncommitted changes warning
if [[ "$CMD_LOWER" =~ git\ reset\ --hard\ head~ ]]; then
    log_blocked "$COMMAND" "git reset --hard HEAD~" "Hard reset attempt"
    block_command "$COMMAND" "Hard reset to previous commits is blocked. Use 'git stash' first or create a backup branch."
fi

# 6. Fork bomb
if echo "$COMMAND" | grep -qE ':\(\)\{' || echo "$CMD_LOWER" | grep -q 'fork bomb'; then
    log_blocked "$COMMAND" "Fork bomb" "Fork bomb attempt"
    block_command "$COMMAND" "Fork bombs are blocked to prevent system resource exhaustion."
fi

# 7. Direct disk write
if [[ "$CMD_LOWER" =~ \>\ /dev/sd[a-z] ]] || [[ "$CMD_LOWER" =~ dd\ if=.*of=/dev/sd[a-z] ]]; then
    log_blocked "$COMMAND" "Direct disk write" "Raw disk write attempt"
    block_command "$COMMAND" "Writing directly to disk devices is blocked to prevent data corruption."
fi

# 8. mkfs commands
if [[ "$CMD_LOWER" =~ mkfs\.ext[0-9]|mkfs\.xfs|mkfs\.btrfs|mkfs\.vfat ]]; then
    log_blocked "$COMMAND" "mkfs" "Filesystem creation attempt"
    block_command "$COMMAND" "Filesystem creation commands are blocked to prevent accidental data loss."
fi

# 9. chmod/chown recursive on root
if [[ "$CMD_LOWER" =~ chmod\ -r\ 777\ / ]] || [[ "$CMD_LOWER" =~ chown\ -r.*\ /$ ]]; then
    log_blocked "$COMMAND" "Recursive chmod/chown on root" "Permission change on root"
    block_command "$COMMAND" "Recursive permission changes on root directory are blocked."
fi

# 10. Curl/wget piped to shell (potential remote code execution)
if [[ "$CMD_LOWER" =~ curl.*\|\ sh ]] || [[ "$CMD_LOWER" =~ wget.*\|\ sh ]] || [[ "$CMD_LOWER" =~ curl.*\|\ bash ]] || [[ "$CMD_LOWER" =~ wget.*\|\ bash ]]; then
    log_blocked "$COMMAND" "Remote script execution" "Piping remote content to shell"
    block_command "$COMMAND" "Piping remote content directly to shell is blocked for security. Download and inspect the script first."
fi

# If we got here, the command is allowed
allow_command