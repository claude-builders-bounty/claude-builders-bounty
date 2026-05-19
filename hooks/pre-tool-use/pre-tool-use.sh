#!/usr/bin/env bash
"""
Claude Code pre-tool-use hook to block destructive bash commands.

This hook blocks the following patterns:
- rm -rf
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without a WHERE clause

It logs blocked attempts to ~/.claude/hooks/blocked.log.
"""

# Read the JSON input from stdin
input=$(cat)

# Extract values using jq (if available) or fallback to bash parsing
# We'll use jq if it's available, otherwise we'll do simple parsing
if command -v jq >/dev/null 2>&1; then
    tool_name=$(echo "$input" | jq -r '.toolName // ""')
    command=$(echo "$input" | jq -r '.toolInput.command // ""')
    project_path=$(echo "$input" | jq -r '.toolInput.projectPath // "'"$PWD"'"')
else
    # Fallback parsing without jq (basic)
    tool_name=$(echo "$input" | grep -o '"toolName":"[^"]*"' | cut -d'"' -f4)
    command=$(echo "$input" | grep -o '"command":"[^"]*"' | cut -d'"' -f4)
    project_path=$(echo "$input" | grep -o '"projectPath":"[^"]*"' | cut -d'"' -f4)
    # If projectPath is empty, use current directory
    if [ -z "$project_path" ]; then
        project_path="$PWD"
    fi
fi

# Patterns to block (case-insensitive)
# We'll check each pattern
blocked=false
reason=""

# Convert command to lowercase for case-insensitive matching
command_lower=$(echo "$command" | tr '[:upper:]' '[:lower:]')

# Check each pattern
if echo "$command_lower" | grep -q "rm\s*-rf"; then
    blocked=true
    reason="Matched pattern: rm -rf"
elif echo "$command_lower" | grep -q "drop\s*table"; then
    blocked=true
    reason="Matched pattern: DROP TABLE"
elif echo "$command_lower" | grep -q "git\s*push\s*--force"; then
    blocked=true
    reason="Matched pattern: git push --force"
elif echo "$command_lower" | grep -q "truncate"; then
    blocked=true
    reason="Matched pattern: TRUNCATE"
elif echo "$command_lower" | grep -q "delete\s*from"; then
    # Check if there's no WHERE after DELETE FROM
    # Find position of "delete from" and see if "where" exists after it
    pos=$(echo "$command_lower" | grep -b -o "delete from" | cut -d: -f1)
    if [ -n "$pos" ]; then
        # Extract substring after "delete from"
        after=${command_lower:$((pos + 10))}
        if ! echo "$after" | grep -q "where"; then
            blocked=true
            reason="DELETE FROM without WHERE clause"
        fi
    fi
fi

if [ "$blocked" = true ]; then
    # Log the blocked command
    log_file="$HOME/.claude/hooks/blocked.log"
    mkdir -p "$(dirname "$log_file")"
    timestamp=$(date -Iseconds)
    echo "$timestamp | $command | $project_path" >> "$log_file"

    # Output JSON to block the command
    cat <<EOF
{
    "hookSpecificOutput": {
        "hookEventName": "pre-tool-use",
        "permissionDecision": "block",
        "permissionDecisionReason": "Blocked destructive command: $reason"
    }
}
EOF
else
    # Allow the command to proceed
    cat <<EOF
{
    "hookSpecificOutput": {
        "hookEventName": "pre-tool-use",
        "permissionDecision": "allow"
    }
}
EOF
fi