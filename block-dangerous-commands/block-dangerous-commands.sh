#!/bin/bash
# Claude Code pre-tool-use hook that blocks destructive bash commands.
#
# Installation:
#     mkdir -p ~/.claude/hooks
#     cp block-dangerous-commands.sh ~/.claude/hooks/
#     chmod +x ~/.claude/hooks/block-dangerous-commands.sh
#
# Usage:
#     This hook is automatically invoked by Claude Code before bash commands.

# Read input from stdin
INPUT=$(cat)

# Extract command and project path
COMMAND=$(echo "$INPUT" | jq -r '.command // empty')
PROJECT_PATH=$(echo "$INPUT" | jq -r '.project_path // empty')

# Log file
LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to check if command is blocked
is_blocked() {
    local cmd="$1"
    local cmd_upper=$(echo "$cmd" | tr '[:lower:]' '[:upper:]')
    
    # Check patterns
    if echo "$cmd" | grep -qiE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)*-[a-zA-Z]*r[a-zA-Z]*\s|rm\s+-rf\s|rm\s+-fr\s|rm\s+--recursive\s+--force\b'; then
        echo "Recursive force delete"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bDROP\s+TABLE\b'; then
        echo "DROP TABLE without safety check"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bTRUNCATE\s+TABLE?\b'; then
        echo "TRUNCATE without safety check"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bDELETE\s+FROM\b(?![\s\S]*WHERE)'; then
        echo "DELETE without WHERE clause"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-[a-zA-Z]*f[a-zA-Z]*\b'; then
        echo "Force push to remote"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bgit\s+push\s+.*--delete\b'; then
        echo "Delete remote branch"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bgit\s+reset\s+--hard\b'; then
        echo "Hard reset (loses changes)"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bgit\s+clean\s+-[a-zA-Z]*f[a-zA-Z]*\b'; then
        echo "Force clean untracked files"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bgit\s+checkout\s+.*--force\b'; then
        echo "Force checkout (loses changes)"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bmkfs\b|\bdd\s+if=|\bformat\s+[a-zA-Z]:'; then
        echo "Disk/filesystem destruction"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bchmod\s+[0-7]*\s+/(usr|etc|var|bin|sbin|lib)\b'; then
        echo "Changing system directory permissions"
        return 0
    fi
    
    if echo "$cmd" | grep -qiE '\bchown\s+.*:.*\s+/(usr|etc|var|bin|sbin|lib)\b'; then
        echo "Changing system directory ownership"
        return 0
    fi
    
    return 1
}

# Main logic
if [ -n "$COMMAND" ]; then
    BLOCKED_REASON=$(is_blocked "$COMMAND")
    
    if [ $? -eq 0 ]; then
        # Command is blocked
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        
        # Log the blocked command
        echo "{\"timestamp\":\"$TIMESTAMP\",\"command\":\"$COMMAND\",\"pattern\":\"$BLOCKED_REASON\",\"project\":\"$PROJECT_PATH\"}" >> "$LOG_FILE"
        
        # Return block decision
        echo "{\"decision\":\"block\",\"reason\":\"🚫 Command blocked: $BLOCKED_REASON. This command was blocked by the safety hook because it could cause irreversible damage.\"}"
        exit 0
    fi
fi

# Allow the command
echo "{\"decision\":\"allow\"}"
exit 0
