#!/bin/bash

# Elite Agency - Destructive Command Blocker
# This script is a pre-execution hook to prevent accidental execution of destructive commands.

# List of blocked patterns
BLOCKED_PATTERNS=(
    "rm -rf /"
        "rm -rf *"
            "DROP TABLE"
                "DROP DATABASE"
                    "git push --force"
                        "git push -f"
                            "mkfs"
                                "dd if="
                                )

                                # Get the command being executed
                                COMMAND="$*"

                                # Check if command contains any blocked pattern
                                for pattern in "${BLOCKED_PATTERNS[@]}"; do
                                    if [[ "$COMMAND" == *"$pattern"* ]]; then
                                            echo -e "\033[0;31m[BLOCKER] CRITICAL: Destructive command detected!\033[0m"
                                                    echo -e "\033[0;31m[BLOCKER] Command: $COMMAND\033[0m"
                                                            echo -e "\033[0;31m[BLOCKER] Reason: Matches pattern '$pattern'\033[0m"
                                                                    echo -e "\033[0;33m[BLOCKER] Execution halted for safety.\033[0m"
                                                                            exit 1
                                                                                fi
                                                                                done

                                                                                # If no blocked patterns found, exit with success
                                                                                exit 0
                                                                                
