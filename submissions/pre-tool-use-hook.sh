#!/bin/bash
# pre-tool-use hook — blocks dangerous bash commands
# Claude Code hooks compatible
# Install: cp pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
HOOKS_DIR="${HOME}/.claude/hooks"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Read JSON input from Claude Code
input=$(cat)

# Extract the command/tool name from JSON
command=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null || echo "")

# If no command, allow
if [ -z "$command" ]; then
    exit 0
fi

# Project path (from input or default)
project_path=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('project_path',''))" 2>/dev/null || echo "unknown")

# Define dangerous patterns (order matters — check more specific first)
DANGEROUS_PATTERNS=(
    "rm -rf /"
    "rm -rf /tmp"
    "DROP TABLE"
    "DROP DATABASE"
    "TRUNCATE TABLE"
    "TRUNCATE"
    "DELETE FROM [a-zA-Z_]+ *;"
    "git push --force"
    "git push -f"
    "rm -rf .git"
    "chmod -R 777"
    "mkfs"
    "dd if="
    ":(){:|:&};"  # fork bomb
)

# Check each dangerous pattern
blocked=false
blocked_pattern=""
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    # Use grep for regex matching (case-insensitive for SQL)
    if echo "$command" | grep -iqE "$pattern" 2>/dev/null; then
        blocked=true
        blocked_pattern="$pattern"
        break
    fi
done

if [ "$blocked" = true ]; then
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log the blocked attempt
    echo "[$timestamp] BLOCKED: '$command' | Pattern: '$blocked_pattern' | Path: $project_path" >> "$LOG_FILE"
    
    # Output blocked message for Claude
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║  HOOK: Command Blocked                                      ║
║  Your command was blocked by the pre-tool-use security hook. ║
║                                                              ║
║  Blocked pattern: DANGEROUS_OPERATION                       ║
║                                                              ║
║  Reason: This command could cause irreversible data loss or  ║
║  security compromise. If you believe this is a false        ║
║  positive, you can:                                         ║
║                                                              ║
║  1. Break down the operation into smaller, safe steps        ║
║  2. Use version control (git) instead of raw file deletion  ║
║  3. Ask the user to confirm before executing destructive     ║
║     operations                                              ║
║                                                              ║
║  This incident has been logged for security audit.           ║
╚══════════════════════════════════════════════════════════════╝

EOF
    exit 1
fi

# Allow safe commands
exit 0
