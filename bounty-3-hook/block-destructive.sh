#!/usr/bin/env bash
# Claude Code pre-tool-use hook — blocks destructive bash commands
# Place in .claude/hooks/pre-tool-use/ directory

set -euo pipefail

# Read the command from stdin
COMMAND=$(cat)

# Commands that are always blocked
BLOCKED_CMDS=("rm -rf /" "rm -rf ~" "rm -rf ." "dd if=" "mkfs" ":(){ :|:& };:")

# Patterns that require confirmation (prefix match)
DANGEROUS_PATTERNS=("rm -rf" "rm -r" "rm -f" "chmod -R 777" "chown -R" ">" ">" "| sh" "| bash" "wget" "curl" "git push --force" "git reset --hard" "drop table" "drop database" "truncate" "sudo ")

for blocked in "${BLOCKED_CMDS[@]}"; do
    if echo "$COMMAND" | grep -qiF "$blocked"; then
        echo "{\"allowed\": false, \"reason\": \"Command '$blocked' is blocked (destructive)\"}"
        exit 0
    fi
done

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "(^|[;&|])$pattern"; then
        echo '{"allowed": false, "reason": "This command matches a dangerous pattern and requires manual confirmation. Run outside Claude Code."}'
        exit 0
    fi
done

echo '{"allowed": true}'
