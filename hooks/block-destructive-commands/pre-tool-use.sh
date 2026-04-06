#!/bin/bash
# Claude Code Pre-tool-use Hook: Block Destructive Commands
# Blocks dangerous bash commands before execution
# Logs to ~/.claude/hooks/blocked.log

set -euo pipefail

HOOKS_DIR="$HOME/.claude/hooks"
LOG_FILE="$HOOKS_DIR/blocked.log"
PROJECT_PATH="${PWD}"

# Ensure log directory exists
mkdir -p "$HOOKS_DIR"

# Read stdin for tool input
INPUT=$(cat)

# Extract tool name and command
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || echo "")

# Only check Bash tool calls
if [[ "$TOOL_NAME" != "Bash" ]]; then
    # Pass through non-bash tools
    echo "$INPUT"
    exit 0
fi

# Extract the command
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")

# Dangerous patterns to block
DANGEROUS_PATTERNS=(
    'rm\s+-rf'
    'rm\s+-fr'
    'rm\s+-[a-z]*r[a-z]*f'
    'DROP\s+TABLE'
    'TRUNCATE\s+TABLE'
    'TRUNCATE\s+[a-zA-Z_]'
    'DELETE\s+FROM'
    'git\s+push\s+--force'
    'git\s+push\s+-f\s+origin'
)

# Check command against dangerous patterns
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        # Log the blocked attempt
        TIMESTAMP=$(date -Iseconds)
        echo "[$TIMESTAMP] BLOCKED: $COMMAND | Project: $PROJECT_PATH" >> "$LOG_FILE"
        
        # Return error to Claude
        cat <<EOF
{"hook_specific_output": {"error_message": "⛔ BLOCKED: This command matches a dangerous pattern and was blocked for safety.

Blocked pattern: $pattern
Command attempted: $COMMAND

Why this was blocked:
- \`rm -rf\` can delete entire filesystems
- \`DROP TABLE\` and \`TRUNCATE\` destroy database data
- \`DELETE FROM\` without WHERE deletes all rows
- \`git push --force\` can overwrite remote history

This attempt has been logged to ~/.claude/hooks/blocked.log

If you really need to run this command, ask the user to run it directly in their terminal."}}
EOF
        exit 2
    fi
done

# Check for DELETE FROM without WHERE clause
if echo "$COMMAND" | grep -qiE 'DELETE\s+FROM'; then
    if ! echo "$COMMAND" | grep -qiE 'WHERE'; then
        # Log the blocked attempt
        TIMESTAMP=$(date -Iseconds)
        echo "[$TIMESTAMP] BLOCKED: $COMMAND (DELETE without WHERE) | Project: $PROJECT_PATH" >> "$LOG_FILE"
        
        cat <<EOF
{"hook_specific_output": {"error_message": "⛔ BLOCKED: DELETE FROM without WHERE clause detected.

Command attempted: $COMMAND

Why this was blocked:
- \`DELETE FROM table\` without a WHERE clause deletes ALL rows
- This is almost never intentional and can cause major data loss

This attempt has been logged to ~/.claude/hooks/blocked.log

If you really need to delete all rows, use TRUNCATE (also blocked) or ask the user to run it directly."}}
EOF
        exit 2
    fi
fi

# Command is safe, pass through
echo "$INPUT"
exit 0
