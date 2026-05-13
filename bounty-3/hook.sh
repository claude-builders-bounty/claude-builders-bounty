#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
# Bounty #3 - https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
#
# Place in ~/.claude/hooks/ and configure in Claude Code settings.
# This hook intercepts dangerous bash commands before execution.

set -uo pipefail

# --- Configuration ---
BLOCKED_LOG="$HOME/.claude/hooks/blocked.log"
HOOK_DIR="$HOME/.claude/hooks"

# Ensure log directory exists
mkdir -p "$HOOK_DIR"

# --- Read Claude Code hook input from stdin ---
INPUT=$(cat)

# Extract the command from the JSON input
# Claude Code hooks receive: {"tool_name": "Bash", "tool_input": {"command": "..."}}
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tool = data.get('tool_name', '')
    if tool != 'Bash':
        sys.exit(1)
    cmd = data.get('tool_input', {}).get('command', '')
    print(cmd)
except:
    sys.exit(1)
" 2>/dev/null) || {
    # Not a Bash tool invocation — allow
    echo '{"decision": "allow"}'
    exit 0
}

# --- Helper: block a command with reason ---
block_command() {
    local REASON="$1"
    local TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    local PROJECT_PATH="${PWD:-unknown}"

    # Log the blocked attempt
    echo "[$TIMESTAMP] BLOCKED | project=$PROJECT_PATH | command=\"$COMMAND\" | reason=$REASON" >> "$BLOCKED_LOG"

    # Return block decision to Claude Code
    local MESSAGE="⛔ Command blocked by safety hook: $REASON

Blocked command: \`$COMMAND\`

If you're sure this is safe, you can run it directly in your terminal.
Log saved to: $BLOCKED_LOG"

    echo "{\"decision\": \"block\", \"reason\": $(echo "$MESSAGE" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))')}"
    exit 0
}

# --- Check 1: rm -rf variants ---
if echo "$COMMAND" | grep -qE 'rm[[:space:]]+(-[[:alpha:]]*f[[:alpha:]]*r|-[[:alpha:]]*r[[:alpha:]]*f)[[:space:]]+\S' 2>/dev/null; then
    block_command "Recursive force delete (rm -rf) detected. This can permanently delete files and directories. Use 'trash' instead, or be specific about what you want to remove."
fi
if echo "$COMMAND" | grep -qE 'rm[[:space:]]+--recursive[[:space:]]+--force[[:space:]]+\S' 2>/dev/null; then
    block_command "Recursive force delete (rm --recursive --force) detected. This can permanently delete files and directories."
fi

# --- Check 2: SQL DROP TABLE ---
if echo "$COMMAND" | grep -qiE 'DROP[[:space:]]+TABLE' 2>/dev/null; then
    block_command "SQL DROP TABLE detected. This permanently deletes an entire database table and all its data."
fi

# --- Check 3: SQL TRUNCATE ---
if echo "$COMMAND" | grep -qiE 'TRUNCATE' 2>/dev/null; then
    block_command "SQL TRUNCATE detected. This permanently deletes all rows from a table."
fi

# --- Check 4: SQL DELETE FROM without WHERE ---
if echo "$COMMAND" | grep -qiE 'DELETE[[:space:]]+FROM' 2>/dev/null; then
    if ! echo "$COMMAND" | grep -qiE 'WHERE' 2>/dev/null; then
        block_command "SQL DELETE FROM without WHERE clause detected. This would delete ALL rows in the table. Always use a WHERE clause to limit deletion scope."
    fi
    # Has WHERE clause — safe, continue
fi

# --- Check 5: Git force push ---
if echo "$COMMAND" | grep -qE 'git[[:space:]]+push.*(--force| -f )' 2>/dev/null; then
    block_command "Git force push detected. This rewrites remote history and can lose other contributors' work. Use --force-with-lease if you must force push."
fi
if echo "$COMMAND" | grep -qE 'git[[:space:]]+push.* -f$' 2>/dev/null; then
    block_command "Git force push (-f) detected. This rewrites remote history and can lose other contributors' work."
fi
if echo "$COMMAND" | grep -qE 'git[[:space:]]+push[[:space:]]+\S+[[:space:]]+\+' 2>/dev/null; then
    block_command "Git force push (+refspec) detected. This rewrites remote history and can lose other contributors' work."
fi

# --- All checks passed, command is safe ---
echo '{"decision": "allow"}'
exit 0
