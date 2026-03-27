#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Claude Code Pre-Tool-Use Hook: Destructive Command Guard   ║
# ║                                                              ║
# ║  Intercepts dangerous bash commands before Claude executes   ║
# ║  them. Blocks: rm -rf, DROP TABLE, git push --force,        ║
# ║  TRUNCATE, DELETE FROM (without WHERE).                      ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool name and command from JSON
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Only check Bash tool commands
if [ -z "$TOOL_NAME" ]; then
  exit 0  # Not a bash command — allow
fi

COMMAND="$TOOL_NAME"
BLOCKED=""
REASON=""

# ─── Pattern Matching ─────────────────────────────────────────

# 1. rm -rf (recursive force delete)
if echo "$COMMAND" | grep -qiP 'rm\s+(-[^\s]*r[^\s]*f|-[^\s]*f[^\s]*r)\b'; then
  BLOCKED="true"
  REASON="Destructive file deletion: 'rm -rf' can irreversibly delete files and directories"
fi

# 2. rm -r / (root deletion)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP 'rm\s+.*-[^\s]*r[^\s]*\s+/(\s|$)'; then
  BLOCKED="true"
  REASON="Root filesystem deletion detected"
fi

# 3. mkfs (format filesystem)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP '\bmkfs\b'; then
  BLOCKED="true"
  REASON="Filesystem formatting command 'mkfs' detected"
fi

# 4. dd with of=/dev (disk overwrite)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP '\bdd\b.*\bof=/dev/'; then
  BLOCKED="true"
  REASON="Direct disk write via 'dd of=/dev/' detected"
fi

# 5. DROP TABLE / DROP DATABASE (SQL)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP '\bDROP\s+(TABLE|DATABASE)\b'; then
  BLOCKED="true"
  REASON="SQL destructive operation: DROP TABLE/DATABASE"
fi

# 6. TRUNCATE TABLE (SQL)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP '\bTRUNCATE\s+TABLE\b'; then
  BLOCKED="true"
  REASON="SQL destructive operation: TRUNCATE TABLE"
fi

# 7. DELETE FROM without WHERE (SQL mass deletion)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP '\bDELETE\s+FROM\b' && ! echo "$COMMAND" | grep -qiP '\bWHERE\b'; then
  BLOCKED="true"
  REASON="SQL mass deletion: DELETE FROM without WHERE clause"
fi

# 8. git push --force (history rewrite) — but NOT --force-with-lease (which is safe)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP 'git\s+push\s+.*--force(?!-with-lease)\b'; then
  BLOCKED="true"
  REASON="Forced git push can rewrite remote history: 'git push --force'"
fi

# 9. git push -f (shorthand force)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP 'git\s+push\s+(-f\b|.*\s-f\b)'; then
  BLOCKED="true"
  REASON="Forced git push can rewrite remote history: 'git push -f'"
fi

# 10. chmod 777 (overly permissive)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP '\bchmod\s+777\b'; then
  BLOCKED="true"
  REASON="Overly permissive file permissions: 'chmod 777' is a security risk"
fi

# 11. > /dev/sda or similar device overwrite
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiP '>\s*/dev/(sd|nvme|hd)'; then
  BLOCKED="true"
  REASON="Direct device overwrite via redirection detected"
fi

# 12. :(){ :|:& };: (fork bomb)
if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qP ':\(\)\s*\{'; then
  BLOCKED="true"
  REASON="Fork bomb pattern detected"
fi

# ─── Decision ─────────────────────────────────────────────────

if [ -n "$BLOCKED" ]; then
  # Log the blocked attempt
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd','unknown'))" 2>/dev/null || echo "unknown")
  echo "[$TIMESTAMP] BLOCKED | project=$PROJECT_PATH | command=$COMMAND | reason=$REASON" >> "$LOG_FILE"

  # Output deny decision as JSON
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "🛡️ BLOCKED by Destructive Command Guard: $REASON. Command: '$COMMAND'"
  }
}
EOF
  exit 0
fi

# Allow safe commands — exit with no output
exit 0
