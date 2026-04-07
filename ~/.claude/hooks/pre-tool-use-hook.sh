#!/bin/bash

# Path for the log file
LOG_FILE="~/.claude/hooks/blocked.log"

# Function to block commands
block_command() {
  echo "Blocked a destructive command: $1" >> $LOG_FILE
  echo "Command '$1' was blocked: Destructive commands are not allowed to execute."
}

# List of destructive patterns
PATTERNS=("rm -rf" "DROP TABLE" "git push --force" "TRUNCATE" "DELETE FROM")

# Check for destructive commands
for pattern in "${PATTERNS[@]}"; do
  if [[ "$1" == *"$pattern"* ]]; then
    block_command "$1"
    exit 1
  fi
done

# If command is not blocked, execute
exec "$@"