#!/bin/bash
# Pre-tool-use hook: Blocks destructive bash commands
# Claude Code hook - runs before every shell command

DESTRUCTIVE_PATTERNS=(
    "rm -rf /"
    "rm -rf --no-preserve-root"
    "dd if=/dev/zero"
    "mkfs\\."
    "fdisk"
    ":(){ :|:& };:"  # Fork bomb
    "> /dev/sda"
    "chmod -R 000 /"
    "mv / /dev/null"
    "wget.*|bash"
    "curl.*|bash"
    "shutdown -h now"
    "reboot"
    "init 0"
    "poweroff"
    "iptables -F"
    "ufw disable"
)

check_command() {
    local cmd="$1"
    for pattern in "${DESTRUCTIVE_PATTERNS[@]}"; do
        if echo "$cmd" | grep -qiE "$pattern"; then
            echo "❌ BLOCKED: Potentially destructive command detected: $cmd"
            echo "Pattern matched: $pattern"
            exit 1
        fi
    done
}

# If called with a command, check it
if [ $# -gt 0 ]; then
    check_command "$*"
fi
