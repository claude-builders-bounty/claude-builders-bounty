#!/bin/bash

# This hook blocks destructive bash commands before they are executed

# Function to log blocked commands
log_blocked_command() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local command="$1"
    local project_path="$2"
    local log_file="$HOME/.claude/hooks/blocked.log"
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$log_file")"
    
    # Log the blocked command
    echo "[$timestamp] Blocked command: $command in project: $project_path" >> "$log_file"
}

# Check if we're in a Claude Code hook context
if [[ $CLAUDE_HOOK_TYPE == "pre-tool-use" ]]; then
    # Check for destructive commands
    case "$TOOL_NAME" in
        "bash"|"shell"|"zsh")
            # Check for destructive patterns
            if [[ "$TOOL_INPUT" == *"rm -rf"* ]] || 
               [[ "$TOOL_INPUT" == *"DROP TABLE"* ]] || 
               [[ "$TOOL_INPUT" == *"git push --force"* ]] || 
               [[ "$TOOL_INPUT" == *"TRUNCATE"* ]] || 
               [[ "$TOOL_INPUT" == *"DELETE FROM"* && "$TOOL_INPUT" != *WHERE* ]]; then
                
                # Log the attempt
                log_blocked_command "$TOOL_INPUT" "$PROJECT_PATH"
                
                # Block the command
                echo "❌ BLOCKED: Dangerous command detected - $TOOL_INPUT"
                echo "This command contains potentially destructive operations and has been blocked for your safety."
                echo "If you need to run this command, please do so manually in your terminal."
                exit 1
            fi
            ;;
        *)
            # Not a bash tool call, let it through
            exit 0
            ;;
    esac
fi

exit 0