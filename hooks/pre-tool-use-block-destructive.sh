 #!/usr/bin/env bash
 # Claude Code pre-tool-use hook: blocks destructive bash commands
 # Install: cp hooks/pre-tool-use-block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.sh
 
 set -euo pipefail
 
 LOG_FILE="${HOME}/.claude/hooks/blocked.log"
 mkdir -p "$(dirname "$LOG_FILE")"
 
 # Read the tool input from stdin (JSON with "command" field for BashTool)
 INPUT=$(cat)
 COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
 
 if [ -z "$COMMAND" ]; then
   exit 0
 fi
 
 BLOCKED=false
 REASON=""
 
 # Pattern checks
 if echo "$COMMAND" | grep -qiE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s'; then
   BLOCKED=true
   REASON="Destructive file deletion: rm -rf is blocked to prevent accidental data loss."
 elif echo "$COMMAND" | grep -qiE '\bDROP\s+TABLE\b'; then
   BLOCKED=true
   REASON="Destructive SQL: DROP TABLE is blocked. Use migrations instead."
 elif echo "$COMMAND" | grep -qiE 'git\s+push\s+.*--force'; then
   BLOCKED=true
   REASON="Dangerous git operation: git push --force can overwrite remote history."
 elif echo "$COMMAND" | grep -qiE '\bTRUNCATE\b'; then
   BLOCKED=true
   REASON="Destructive SQL: TRUNCATE is blocked. Use DELETE with WHERE or migrations."
 elif echo "$COMMAND" | grep -qiE '\bDELETE\s+FROM\b' && ! echo "$COMMAND" | grep -qiE '\bWHERE\b'; then
   BLOCKED=true
   REASON="Unsafe SQL: DELETE FROM without WHERE clause would delete all rows."
 fi
 
 if [ "$BLOCKED" = true ]; then
   TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
   PROJECT_PATH="${CLAUDE_PROJECT_DIR:-$(pwd)}"
   echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
   
   # Output block decision as JSON for Claude Code
   cat <<EOF
 {
   "decision": "block",
   "reason": "${REASON}"
 }
 EOF
   exit 0
 fi
 
 # Allow the command
 echo '{"decision":"allow"}'
 exit 0
