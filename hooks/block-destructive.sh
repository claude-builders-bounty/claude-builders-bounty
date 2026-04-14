#!/usr/bin/env bash
# block-destructive.sh — Claude Code pre-tool-use hook
# Blocks dangerous bash commands before execution
# Install: cp -r hooks ~/.claude/hooks/

set -euo pipefail

# Read the command from stdin (Claude Code passes tool input via stdin)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null || true)

if [ -z "$COMMAND" ]; then
    exit 0
fi

# Patterns to block
BLOCK_PATTERNS=(
    "rm -rf /"
    "rm -rf ~"
    "rm -rf \*"
    "DROP TABLE"
    "TRUNCATE"
    "DELETE FROM"
    "git push --force"
    "git push -f"
    "mkfs"
    "dd if="
    "> /dev/sd"
    "chmod -R 777 /"
    ":(){ :|:& };:"
)

# Patterns that are safe (have safeguards)
SAFE_PATTERNS=(
    "rm -rf .*--preserve-root"
    "rm -rf .*--no-preserve-root"
    "DROP TABLE IF EXISTS"
    "DELETE FROM.*WHERE"
    "git push --force-with-lease"
)

LOG_FILE="$HOME/.claude/hooks/blocked.log"
PROJECT_PATH="${PWD}"

blocked=false
reason=""

for pattern in "${BLOCK_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        # Check if it has a safe override
        safe=false
        for safe_pat in "${SAFE_PATTERNS[@]}"; do
            if echo "$COMMAND" | grep -qiE "$safe_pat"; then
                safe=true
                break
            fi
        done
        
        if ! $safe; then
            blocked=true
            reason="Matched dangerous pattern: ${pattern}"
            break
        fi
    fi
done

if $blocked; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[${TIMESTAMP}] BLOCKED | Pattern: ${reason} | Command: ${COMMAND} | Project: ${PROJECT_PATH}" >> "$LOG_FILE"
    
    # Output structured error for Claude
    cat <<EOF
{
  "decision": "block",
  "reason": "This command matches a dangerous pattern and has been blocked for safety.\n\nMatched: ${reason}\nCommand: ${COMMAND}\n\nIf this is intentional, the user should run it manually outside of Claude Code."
}
EOF
    exit 2
fi

# Allow the command
echo '{"decision": "allow"}'
exit 0
