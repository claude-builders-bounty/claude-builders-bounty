#!/bin/bash

# Pre-tool-use hook to block destructive bash commands
# This script checks if a command is potentially dangerous and blocks it

# Get the command being executed
command="$1"

# Check for destructive patterns
case "$command" in
  *'rm -rf/'*|*'rm -rf '*)
    echo "BLOCKED: rm -rf command detected. This command is potentially destructive and has been blocked."
    echo "$(date): Blocked command: $command" >> ~/.claude/hooks/blocked.log
    exit 1
    ;;
  *'DROP TABLE '*|*'DROP TABLE'*)
    echo "BLOCKED: DROP TABLE command detected. This command is potentially destructive and has been blocked."
    echo "$(date): Blocked command: $command" >> ~/.claude/hooks/blocked.log
    exit 1
    ;;
  *'git push --force'*)
    echo "BLOCKED: git push --force command detected. This command is potentially destructive and has been blocked."
    echo "$(date): Blocked command: $command" >> ~/.claude/hooks/blocked.log
    exit 1
    ;;
  *'TRUNCATE '*|*'TRUNCATE'*)
    echo "BLOCKED: TRUNCATE command detected. This command is potentially destructive and has been blocked."
    echo "$(date): Blocked command: $command" >> ~/.claude/hooks/blocked.log
    exit 1
    ;;
  *'DELETE FROM '*)
    # Check if it's a DELETE FROM without WHERE
    if [[ ! "$command" =~ .*WHERE.* ]]; then
      echo "BLOCKED: DELETE FROM without WHERE clause detected. This command is potentially destructive and has been blocked."
      echo "$(date): Blocked command: $command" >> ~/.claude/hooks/blocked.log
      exit 1
    fi
    ;;
esac

# If we get here, the command is not blocked
echo "Command allowed: $command"

# Log the allowed command
echo "$(date): Allowed command: $command" >> ~/.claude/hooks/allowed.log

exit 0