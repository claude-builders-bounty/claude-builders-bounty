#!/usr/bin/env bash
# Pre-tool-use hook: blocks destructive bash commands before execution.
#
# Reads tool call JSON from stdin.  When the tool is Bash and the command
# matches a blocked pattern, the hook returns exit code 2 and writes a
# blocking message to stdout.  Otherwise it returns 0 (allow).
#
# Installation:  ln -s "$PWD/hooks/pre-tool-use/block-destructive.sh" ~/.claude/hooks/pre-tool-use/

set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
HOOK_NAME="block-destructive"

# Ensure log dir exists
mkdir -p "$(dirname "$LOG_FILE")"

# Read the JSON payload from stdin
PAYLOAD=$(cat)

# Extract the command if this is a Bash tool call
TOOL_NAME=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

if [ "$TOOL_NAME" != "Bash" ]; then
    echo "$PAYLOAD"
    exit 0
fi

COMMAND=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
CWD=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || pwd)

# Normalize whitespace for pattern matching
NORMALIZED=$(echo "$COMMAND" | tr -s '[:space:]' ' ' | xargs)

BLOCKED=false
REASON=""

# Pattern: rm -rf (dangerous recursive force remove)
if echo "$NORMALIZED" | grep -qiE '\brm\s+-[a-z]*r[a-z]*f[a-z]*\b'; then
    BLOCKED=true
    REASON="rm -rf (recursive force remove)"
fi

# Pattern: DROP TABLE
if echo "$NORMALIZED" | grep -qiE '\bDROP\s+TABLE\b'; then
    BLOCKED=true
    REASON="DROP TABLE (destructive database operation)"
fi

# Pattern: TRUNCATE
if echo "$NORMALIZED" | grep -qiE '\bTRUNCATE\b'; then
    BLOCKED=true
    REASON="TRUNCATE (destructive database operation)"
fi

# Pattern: DELETE FROM without WHERE
if echo "$NORMALIZED" | grep -qiE '\bDELETE\s+FROM\b'; then
    if ! echo "$NORMALIZED" | grep -qiE '\bWHERE\b'; then
        BLOCKED=true
        REASON="DELETE FROM without WHERE clause (would delete all rows)"
    fi
fi

# Pattern: git push --force variants
if echo "$NORMALIZED" | grep -qiE '\bgit\s+push\b.*(-f|--force|--force-with-lease)'; then
    BLOCKED=true
    REASON="git push --force (destructive remote operation)"
fi

if [ "$BLOCKED" = true ]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Log the blocked attempt
    cat >> "$LOG_FILE" << LOGENTRY
[$TIMESTAMP] BLOCKED: $REASON
  Command: $COMMAND
  Project: $CWD
LOGENTRY

    # Tell Claude why it was blocked (stdout becomes the hook response)
    cat << BLOCKMSG
{
  "hookSpecificOutput": {
    "hookEventName": "pre-tool-use",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$REASON — this command has been blocked for safety. If you need to run it, disable the hook or use a safer alternative."
  }
}
BLOCKMSG
    exit 2
fi

# Allow the command
echo "$PAYLOAD"
exit 0
