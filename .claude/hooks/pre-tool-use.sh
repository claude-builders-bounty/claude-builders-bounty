#!/bin/bash

# Pre-tool-use hook that blocks dangerous bash commands.

LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Function to log blocked attempts
log_blocked() {
    echo "$(date): Attempted command '$1' blocked in project path '$PWD'" >> "$LOG_FILE"
    echo "Command '$1' has been blocked due to safety concerns."
}

# List of dangerous commands to block
DANGEROUS_COMMANDS=("rm -rf" "DROP TABLE" "git push --force" "TRUNCATE" "DELETE FROM")

# Function to check if command is dangerous

echo "Checking if command is dangerous: "$1"
is_dangerous() {
    for cmd in "${DANGEROUS_COMMANDS[@]}"; do
        if [[ "$1" == *"$cmd"* ]]; then
            return 0 # Command is dangerous
        fi
    done
    return 1 # Command is safe
}

# Main execution block

echo "Hook triggered with arguments: $@"
for cmd in "$@"; do
    if is_dangerous "$cmd"; then
        echo "Blocked command: $cmd"
        log_blocked "$cmd"
        exit 1 # Block the execution
    fi
done

# If safe, execute the command
exec "$@"