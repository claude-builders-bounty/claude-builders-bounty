#!/bin/bash
# pre-tool-use hook: block destructive bash commands in Claude Code
# Installation: cp this file to ~/.claude/hooks/pre-tool-use/block-destructive-commands.sh
# Logs every blocked attempt to ~/.claude/hooks/blocked.log
#
# Claude Code hook format:
#   - stdin:  JSON object with the tool use request
#   - stdout: JSON object to pass through (unmodified) or exit non-zero to block

set -e

read -r input

# Extract the command string from the JSON input (Bash_2024 tool or similar)
cmd=$(echo "$input" | jq -r '.command // .bash // .cmd // ""' 2>/dev/null)

# If we can't parse a command, pass through (don't block safe operations)
if [ -z "$cmd" ]; then
    echo "$input"
    exit 0
fi

logfile="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$logfile")"

block_cmd() {
    local pattern="$1"
    local cmd="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local project_path="${PWD:-unknown}"
    local entry="[${timestamp}] BLOCKED | project: ${project_path} | pattern: ${pattern} | command: ${cmd}"
    echo "$entry" >> "$logfile"
    echo ""
    echo "SECURITY: Blocked by pre-tool-use hook"
    echo ""
    echo "The following command was blocked because it matched a destructive pattern:"
    echo "  Pattern: ${pattern}"
    echo "  Command: ${cmd:0:200}"
    echo ""
    echo "This hook prevents accidental destructive operations."
    echo "If you intentionally need to run this command, disable the hook temporarily:"
    echo "  mv ~/.claude/hooks/pre-tool-use/block-destructive-commands.sh ~/.claude/hooks/pre-tool-use/block-destructive-commands.sh.disabled"
    echo ""
    echo "Block logged to: ${logfile}"
    exit 1
}

# Pattern-based checks (grep -E compatible)
if echo "$cmd" | grep -qiE "rm\s+-rf\s+/"; then
    block_cmd "rm -rf /" "$cmd"
fi

# Block any rm -rf on root or system paths (safe: /var/log is fine, / or /etc is not)
if echo "$cmd" | grep -qiE "(^|\s)rm\s+(-rf|--recursive)\s+(\/|(\/\w+){1,2}\b)"; then
    block_cmd "rm -rf system path" "$cmd"
fi

if echo "$cmd" | grep -qiE "DROP\s+(TABLE|DATABASE)"; then
    block_cmd "DROP TABLE/DATABASE" "$cmd"
fi

if echo "$cmd" | grep -qiE "TRUNCATE\s+"; then
    block_cmd "TRUNCATE" "$cmd"
fi

if echo "$cmd" | grep -qiE "git push\s+(--force|-f)\b"; then
    block_cmd "git push --force" "$cmd"
fi

if echo "$cmd" | grep -qiE "sudo\s+rm\s+"; then
    block_cmd "sudo rm" "$cmd"
fi

if echo "$cmd" | grep -qiE "chmod\s+-R\s+777"; then
    block_cmd "chmod -R 777" "$cmd"
fi

if echo "$cmd" | grep -qiE "mkfs\."; then
    block_cmd "mkfs (filesystem format)" "$cmd"
fi

if echo "$cmd" | grep -qiE "dd\s+if=/dev/zero"; then
    block_cmd "dd if=/dev/zero (disk wipe)" "$cmd"
fi

if echo "$cmd" | grep -qiE ">\s*/dev/sd[a-z]"; then
    block_cmd "direct disk write" "$cmd"
fi

if echo "$cmd" | grep -qiE "mv\s+/\s+"; then
    block_cmd "mv / (possible root move)" "$cmd"
fi

# Fork bomb detection
if echo "$cmd" | grep -qiE ":\s*\(\s*\)\s*\{"; then
    block_cmd "fork bomb" "$cmd"
fi

# DELETE FROM table without WHERE clause (two-step check)
if echo "$cmd" | grep -qiE "DELETE FROM"; then
    # Check if WHERE is also present
    if ! echo "$cmd" | grep -qiE "\bWHERE\b"; then
        block_cmd "DELETE FROM without WHERE" "$cmd"
    fi
fi

# No destructive patterns found — pass through
echo "$input"
exit 0