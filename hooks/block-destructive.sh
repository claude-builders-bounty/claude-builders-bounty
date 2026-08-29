 #!/usr/bin/env bash
 # Pre-tool-use hook for Claude Code: blocks destructive bash commands.
 # Install: cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
 
 set -euo pipefail
 
 LOG_FILE="${HOME}/.claude/hooks/blocked.log"
 mkdir -p "$(dirname "$LOG_FILE")"
 touch "$LOG_FILE"
 
 # Read the tool input from stdin (JSON with "command" field)
 INPUT=$(cat)
 CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)
 
 if [ -z "$CMD" ]; then
   exit 0
 fi
 
 BLOCKED=0
 REASON=""
 
 # Normalize command for matching
 NORM_CMD=$(echo "$CMD" | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]]\+/ /g')
 
 # Pattern checks
 if echo "$NORM_CMD" | grep -qE 'rm\s+-[a-z]*r[a-z]*f|rm\s+-[a-z]*f[a-z]*r'; then
   BLOCKED=1
   REASON="Destructive recursive force delete (rm -rf)"
 elif echo "$NORM_CMD" | grep -qiE '\bdrop\s+table\b'; then
   BLOCKED=1
   REASON="SQL DROP TABLE statement"
 elif echo "$NORM_CMD" | grep -qE 'git\s+push\s+.*--force|git\s+push\s+-f'; then
   BLOCKED=1
   REASON="Force push to remote (git push --force)"
 elif echo "$NORM_CMD" | grep -qiE '\btruncate\s+'; then
   BLOCKED=1
   REASON="SQL TRUNCATE statement"
 elif echo "$NORM_CMD" | grep -qiE '\bdelete\s+from\s+[a-z_]+\s*$|\bdelete\s+from\s+[a-z_]+\s+where\s*;\s*$'; then
   BLOCKED=1
   REASON="DELETE FROM without WHERE clause"
 fi
 
 if [ "$BLOCKED" -eq 1 ]; then
   TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
   PROJECT_PATH=$(pwd)
   echo "${TIMESTAMP} | ${PROJECT_PATH} | ${REASON} | ${CMD}" >> "$LOG_FILE"
   
   # Output structured rejection for Claude Code
   cat <<EOF
 {
   "decision": "block",
   "reason": "⛔ Command blocked by safety hook: ${REASON}. This command matches a destructive pattern that could cause data loss. If this is intentional, please break it into safer steps or use an alternative approach."
 }
 EOF
   exit 0
 fi
 
 # Allow the command
 echo '{"decision": "allow"}'
 exit 0
