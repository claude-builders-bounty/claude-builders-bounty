#!/usr/bin/env bash
# pre-tool-use.sh - Claude Code pre-tool-use hook that blocks destructive bash
# Place in .claude/hooks/pre-tool-use.sh and run: chmod +x .claude/hooks/pre-tool-use.sh

set -euo pipefail

# Block these patterns in bash commands
BLOCKED_PATTERNS=(
    "rm -rf /"
    "rm -rf /*"
    "mkfs\."
    "dd if="
    "> /dev/"
    "chmod -R 000"
    ":(){ :|:& };:"     # fork bomb
    "wget .*\|.*bash"
    "curl .*\|.*bash"
    "git reset --hard HEAD"
    "DROP TABLE"
    "DROP DATABASE"
)

# Allow these explicitly
ALLOWED_COMMANDS=(
    "rm -rf node_modules"
    "rm -rf .next"
    "rm -rf dist"
    "rm -rf build"
    "rm -rf .cache"
    "rm -rf target"
    "git reset --hard HEAD~1"
    "git reset --hard origin/main"
)

is_allowed() {
    local cmd="$1"
    for allowed in "${ALLOWED_COMMANDS[@]}"; do
        if [[ "$cmd" == *"$allowed"* ]]; then
            return 0
        fi
    done
    return 1
}

# Claude Code passes the command as JSON on stdin
read -r input

# Extract tool_use and command
tool_use=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_use',''))" 2>/dev/null || echo "")
command_text=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command','').lower())" 2>/dev/null || echo "")

# Only intercept bash tool calls
if [ "$tool_use" != "bash" ]; then
    echo "$input"
    exit 0
fi

# Check blocked patterns
if ! is_allowed "$command_text"; then
    for pattern in "${BLOCKED_PATTERNS[@]}"; do
        if echo "$command_text" | grep -qiE "$pattern"; then
            echo "{\\"tool_use\\": \\"bash\\", \\"command\\": \\"echo '[BLOCKED] Destructive command detected: $pattern'\\"}"
            exit 0
        fi
    done
fi

# Pass through
echo "$input"
