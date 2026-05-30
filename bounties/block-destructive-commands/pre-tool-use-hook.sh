#!/usr/bin/env bash
# pre-tool-use-hook.sh — Blocks dangerous bash commands before execution
# Install: cp this to ~/.claude/hooks/ and chmod +x
set -euo pipefail

BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$BLOCKED_LOG")"

# Read the command from stdin (Claude Code sends it as JSON)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

[[ -z "$COMMAND" ]] && exit 0

# Normalize: lowercase, collapse whitespace
NORMALIZED=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]' | sed 's/  */ /g')

BLOCKED=""

# Check destructive patterns
if echo "$NORMALIZED" | grep -qE '(^|\|)\s*rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\s'; then
    BLOCKED="rm -rf (recursive force delete)"
elif echo "$NORMALIZED" | grep -qE '(^|\|)\s*rm\s+(-[a-z]*r)\s'; then
    BLOCKED="rm -r (recursive delete)"
elif echo "$NORMALIZED" | grep -qiE '\bdrop\s+table\b'; then
    BLOCKED="DROP TABLE (destroys table and data)"
elif echo "$NORMALIZED" | grep -qiE '\bdrop\s+database\b'; then
    BLOCKED="DROP DATABASE (destroys entire database)"
elif echo "$NORMALIZED" | grep -qiE '\btruncate\b'; then
    BLOCKED="TRUNCATE (deletes all rows)"
elif echo "$NORMALIZED" | grep -qiE '\bdelete\s+from\b' && ! echo "$NORMALIZED" | grep -qiE '\bwhere\b'; then
    BLOCKED="DELETE FROM without WHERE (deletes all rows)"
elif echo "$NORMALIZED" | grep -qE 'git\s+push\s+.*--force'; then
    BLOCKED="git push --force (overwrites remote history)"
elif echo "$NORMALIZED" | grep -qE 'git\s+push\s+.*-f\b'; then
    BLOCKED="git push -f (overwrites remote history)"
elif echo "$NORMALIZED" | grep -qE 'git\s+reset\s+.*--hard'; then
    BLOCKED="git reset --hard (discards all uncommitted changes)"
elif echo "$NORMALIZED" | grep -qE 'git\s+clean\s+.*-fd'; then
    BLOCKED="git clean -fd (deletes all untracked files)"
elif echo "$NORMALIZED" | grep -qE 'mkfs\.'; then
    BLOCKED="mkfs (formats filesystem, destroys all data)"
elif echo "$NORMALIZED" | grep -qE '^\s*shutdown\b|^\s*reboot\b|^\s*init\s+0'; then
    BLOCKED="shutdown/reboot (system power command)"
fi

if [[ -n "$BLOCKED" ]]; then
    # Log the blocked attempt
    echo "[$(date -Iseconds)] BLOCKED: $BLOCKED | COMMAND: $COMMAND | PWD: $(pwd)" >> "$BLOCKED_LOG"
    
    # Output rejection JSON for Claude Code
    cat <<JSON
{
  "decision": "block",
  "reason": "BLOCKED: $BLOCKED — This command is too destructive to run automatically. If you really need to run it, ask the user to execute it manually. See $BLOCKED_LOG for details."
}
JSON
    exit 0
fi

# Allow the command
exit 0
