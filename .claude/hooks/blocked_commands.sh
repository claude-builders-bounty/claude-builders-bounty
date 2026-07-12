#!/bin/bash

# Claude Code pre-tool-use hook that blocks destructive bash commands
#
# Installation:
# 1. Make sure this file is executable: chmod +x block_destructive_commands.sh
# 2. Move this file to ~/.claude/hooks/
#
# This hook blocks destructive commands like:
# - rm -rf
# - DROP TABLE
# - git push --force
# - TRUNCATE
# - DELETE FROM (without WHERE clause)
#
# It will log every blocked attempt to ~/.claude/hooks/blocked.log

main() {
    local command="$1"
    local project_path="$2"
    
    # Check if command is destructive
    is_destructive() {
        case "$1" in
            *"rm -rf"* | *"rm -rf/"* | "rm -rf "* | *"; rm -rf "* | "rm -rf;"*) return 0 ;;
            *"DROP TABLE"* | *"; DROP TABLE "* | "DROP TABLE;"*) return 0 ;;
            *"git push --force"* | *"git push --force "* | *"; git push --force "* | "git push --force;"*) return 0 ;;
            *"TRUNCATE"* | *"TRUNCATE "* | *"; TRUNCATE "* | "TRUNCATE;"*) return 0 ;;
            *"DELETE FROM"*";"*) return 1 ;;  # Only block if no WHERE clause
            *"DELETE FROM"*)
                if ! [[ "$1" == *"WHERE"* ]] && [[ "$1" == *"DELETE FROM"* ]]; then
                    return 0  # No WHERE clause - block it
                fi
                ;;
        esac
        return 1
    }
    
    if is_destructive "$command"; then
        # Log the blocked attempt
        echo "$(date '+%Y-%m-%d %H:%M:%S') Blocked command: $command | Project: $project_path" >> ~/.claude/hooks/blocked.log 2>&1
        echo "Blocked execution of destructive command: $command" >&2
        echo "This command has been blocked for your safety." >&2
        echo "Blocked commands are logged to ~/.claude/hooks/blocked.log" >&2
        exit 1
    fi
    
    exit 0
}

# Call main with all arguments
main "$@"