#!/bin/bash

# Block Destructive Bash Commands Hook
# This script checks a command against a list of destructive patterns.
# Usage: ./pre-tool-use.sh "command to check"

COMMAND="$1"
PATTERNS_FILE="$(dirname "$0")/destructive_patterns.txt"

if [ -z "$COMMAND" ]; then
    echo "No command provided to check."
    exit 0
fi

# Check for matches
while IFS= read -r pattern || [ -n "$pattern" ]; do
    if [[ "$COMMAND" =~ $pattern ]]; then
        echo "Error: Command blocked by safety hook: '$COMMAND'" >&2
        echo "Matches destructive pattern: $pattern" >&2
        exit 1
    fi
done < "$PATTERNS_FILE"

exit 0
