#!/bin/bash

# Simple unit test script for hook
HOOK="./pre-tool-use.sh"

echo '{"command": "ls -la"}' | bash "$HOOK" > /dev/null
if [ $? -ne 0 ]; then
    echo "Failed: Blocked normal command"
    exit 1
fi

echo '{"command": "rm -rf /tmp"}' | bash "$HOOK" > /dev/null
if [ $? -eq 0 ]; then
    echo "Failed: Allowed rm -rf"
    exit 1
fi

echo '{"command": "DELETE FROM users"}' | bash "$HOOK" > /dev/null
if [ $? -eq 0 ]; then
    echo "Failed: Allowed DELETE FROM without WHERE"
    exit 1
fi

echo "All tests passed!"
