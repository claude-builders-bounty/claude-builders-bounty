#!/bin/bash

# Claude Code pre-tool-use hook to block destructive bash commands
# Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM (without WHERE)

# Log file for blocked commands
LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Create log file if it doesn't exist
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# Function to log blocked commands
log_blocked_command() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local command="$1"
    local project_path="$2"
    echo "$timestamp - BLOCKED - $command - $project_path" >> "$LOG_FILE"
}

# Check if we should block based on Claude's working directory
if [ -n "$CLAUDE_WORKING_DIRECTORY" ]; then
    project_path="$CLAUDE_WORKING_DIRECTORY"
else
    project_path="$(pwd)"
fi

# Check if the command contains destructive patterns
if [[ "$CLAUDE_TOOL_USE_COMMAND" == *"rm -rf"* ]]; then
    log_blocked_command "rm -rf" "$project_path"
    echo " blocked: rm -rf command detected"
    exit 1
elif [[ "$CLAUDE_TOOL_USE_COMMAND" == *"DROP TABLE"* ]]; then
    log_blocked_command "DROP TABLE" "$project_path"
    echo " blocked: DROP TABLE command detected"
    exit 1
elif [[ "$CLAUDE_TOOL_USE_COMMAND" == *"git push --force"* ]]; then
    log_blocked_command "git push --force" "$project_path"
    echo " blocked: git push --force command detected"
    exit 1
elif [[ "$CLAUDE_TOOL_USE_COMMAND" == *"TRUNCATE "* ]]; then
    log_blocked_command "TRUNCATE" "$project_path"
    echo " blocked: TRUNCATE command detected"
    exit 1
elif [[ "$CLAUDE_TOOL_USE_COMMAND" == *"DELETE FROM "* ]] && ! [[ "$CLAUDE_TOOL_USE_COMMAND" == *" WHERE "* ]]; then
    log_blocked_command "DELETE FROM without WHERE" "$project_path"
    echo " blocked: DELETE FROM without WHERE clause detected"
    exit 1
fi

# Additional checks for more complex patterns

# Check for rm -rf in a more comprehensive way
if [[ "$CLAUDE_TOOL_USE_COMMAND" =~ rm[[:space:]]+(-[[:alpha:]]*)?[[:space:]]*-[[:alpha:]]*r[[:alpha:]]*[[:space:]]+-[[:alpha:]]*f[[:alpha:]]* ]] || \
   [[ "$CLAUDE_TOOL_USE_COMMAND" =~ rm[[:space:]]+(-[[:alpha:]]*)?[[:space:]]*-[[:alpha:]]*f[[:alpha:]]*[[:space:]]+-[[:alpha:]]*r[[:alpha:]]* ]]; then
    log_blocked_command "rm -rf variant" "$project_path"
    echo " blocked: rm -rf variant detected"
    exit 1
fi

# Check for DROP TABLE
if [[ "$CLAUDE_TOOL_USE_COMMAND" =~ DROP[[:space:]]+TABLE ]]; then
    log_blocked_command "DROP TABLE" "$project_path"
    echo " blocked: DROP TABLE command detected"
    exit 1
fi

# Check for git push --force
if [[ "$CLAUDE_TOOL_USE_COMMAND" == *"git push --force"* ]] || [[ "$CLAUDE_TOOL_USE_COMMAND" == *"git push"* ]] && [[ "$CLAUDE_TOOL_USE_COMMAND" == *" --force"* ]]; then
    log_blocked_command "git push --force" "$project_path"
    echo " blocked: git push --force command detected"
    exit 1
fi

# Check for TRUNCATE
if [[ "$CLAUDE_TOOL_USE_COMMAND" =~ TRUNCATE ]]; then
    log_blocked_command "TRUNCATE" "$project_path"
    echo " blocked: TRUNCATE command detected"
    exit 1
fi

# Check for DELETE FROM without WHERE
if [[ "$CLAUDE_TOOL_USE_COMMAND" =~ DELETE[[:space:]]+FROM ]] && ! [[ "$CLAU2DE_TOOL_USE_COMMAND" =~ WHERE ]]; then
    log_blocked_command "DELETE FROM without WHERE" "$project_path"
    echo " blocked: DELETE FROM without WHERE clause"
    exit 1
fi

# If we get here, the command is allowed
echo " allowed"