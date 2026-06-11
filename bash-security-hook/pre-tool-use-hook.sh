#!/bin/bash
# Pre-Tool-Use Hook - Blocks destructive bash commands
# Bounty #3

BLOCKED_PATTERNS=(
    "rm -rf /"
    "rm -rf --no-preserve-root /"
    "dd if=.* of=/dev/"
    "mkfs\."
    ":(){ :|:& };:"
    "chmod 777 /"
    "chmod -R 777 /"
    "wget.*| sh"
    "curl.*| bash"
    "> /dev/sda"
    "shutdown -h now"
    "reboot"
    "sudo rm -rf"
    "git push --force origin main"
)

check_command() {
    local cmd="$*"
    for pattern in "${BLOCKED_PATTERNS[@]}"; do
        if echo "$cmd" | grep -qi "$pattern"; then
            echo "[BLOCKED] $cmd"
            exit 1
        fi
    done
}

if [ $# -gt 0 ]; then
    check_command "$@"
    exec "$@"
fi
