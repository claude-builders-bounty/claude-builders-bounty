#!/bin/bash
# Pre-tool-use hook to block destructive bash commands
# Install: ~/.claude/hooks/pre-tool-use

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read the command from stdin (Claude Code passes tool use request)
INPUT=$(cat)

# Extract command if it's a bash command
COMMAND=$(echo "$INPUT" | jq -r '.tool.use.bash.command // empty' 2>/dev/null)

if [ -z "$COMMAND" ]; then
    # Not a bash command, allow
    exit 0
fi

# List of dangerous patterns
DANGEROUS_PATTERNS=(
    "rm -rf"
    "rm -fr"
    "rm -rf /"
    "DROP TABLE"
    "DROP DATABASE"
    "TRUNCATE"
    "DELETE FROM.*;"
    "git push --force"
    "git push --force-with-lease"
    ":(){:|:&};:"
    "mkfs"
    "dd if=/dev/zero"
    "chmod -R 777"
    "chown -R"
    ":(){ :|:& };:"
)

# Check for dangerous patterns
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        # Log the blocked attempt
        echo "$(date -Iseconds)|BLOCKED|$COMMAND|$(pwd)" >> "$LOG_FILE"
        
        # Output clear message to Claude
        cat << BLOCKED_MSG
⚠️ **COMMAND BLOCKED** ⚠️

The following command was blocked for safety reasons:

\`\`\`
$COMMAND
\`\`\`

**Reason**: Matches dangerous pattern: \`$pattern\`

This command could:
- Delete files irreversibly
- Destroy databases
- Force-push and overwrite history
- Cause system damage

**What to do**:
1. Review the command carefully
2. Use safer alternatives (e.g., \`rm\` without \`-rf\`, use \`git push\` without \`--force\`)
3. If you're certain this is safe, run it manually in your terminal

Logged to: \`$LOG_FILE\`
BLOCKED_MSG
        
        exit 1
    fi
done

# Command is safe, allow
exit 0
