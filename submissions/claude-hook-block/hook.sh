#!/bin/bash
# Pre-tool-use hook: Blocks destructive bash commands
# Add to your Claude Code hooks config

TOOL_NAME="$1"
TOOL_ARGS="$2"

# Only check bash tool
if [[ "$TOOL_NAME" != "bash" ]]; then
    exit 0
fi

# Dangerous patterns
BLOCKED_PATTERNS=(
    "rm -rf"
    "rm -r /"
    "rm -f /"
    "rm /"
    "sudo rm"
    "> /dev/sda"
    "dd if=/dev/"
    "mkfs"
    "shutdown"
    "reboot"
    "halt"
    "chmod 777"
    "chmod -R 777"
    "chown -R"
    "curl.*|.*sh"
    "wget.*|.*sh"
    "git push --force"
    "git reset --hard"
    "git clean -fd"
    "DROP TABLE"
    "DROP DATABASE"
    "DELETE FROM.*WHERE"
    "TRUNCATE"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$TOOL_ARGS" | grep -qiE "$pattern"; then
        echo "BLOCKED: Command matches dangerous pattern: $pattern"
        echo "Command: $TOOL_ARGS"
        exit 1
    fi
done

exit 0
