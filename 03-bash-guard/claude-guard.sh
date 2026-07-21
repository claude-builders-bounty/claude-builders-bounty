#!/usr/bin/env bash
# claude-guard.sh — Block destructive bash commands
set -euo pipefail

BLOCKED=(
    "rm -rf /" "rm -rf ~" "rm -rf ." "rm -rf \$HOME"
    "> /dev/sda" "dd if=.*of=/dev/"
    "mkfs." ":(){ :|:& };:"
    "chmod -R 777 /" "chown -R .* /"
    "git push --force origin main" "git push --force origin master"
    "DROP TABLE" "DELETE FROM .* WHERE .*1=1"
    "shutdown" "reboot" "halt"
)

claude_guard() {
    local cmd="$BASH_COMMAND"
    for p in "${BLOCKED[@]}"; do
        if [[ "$cmd" =~ $p ]]; then
            echo "BLOCKED: Destructive command: $cmd" >&2
            echo "  Matched pattern: $p" >&2
            return 1
        fi
    done
}

enable_guard() { trap 'claude_guard' DEBUG; echo "Guard enabled"; }
disable_guard() { trap - DEBUG; echo "Guard disabled"; }

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    enable_guard
fi

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        enable)  enable_guard; bash ;;
        disable) disable_guard ;;
        *)       echo "Usage: source claude-guard.sh  (or: bash claude-guard.sh enable)";;
    esac
fi
