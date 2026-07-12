Based on the issue, I need to create a pre-tool-use hook for Claude Code that blocks destructive bash commands. Since the repo only contains `LICENSE` and `README.md`, I'll create the hook script and update the README.

```diff
--- /dev/null
+++ b/hooks/pre-tool-use.sh
@@ -0,0 +1,112 @@
+#!/usr/bin/env bash
+# Claude Code pre-tool-use hook: blocks destructive bash commands
+# Installation: copy to ~/.claude/hooks/pre-tool-use.sh and chmod +x
+
+set -euo pipefail
+
+LOG_FILE="$HOME/.claude/hooks/blocked.log"
+HOOK_DIR="$HOME/.claude/hooks"
+
+# Ensure hook directory and log file exist
+mkdir -p "$HOOK_DIR"
+touch "$LOG_FILE"
+
+# Read the JSON input from stdin (Claude Code passes tool-use events as JSON)
+INPUT=$(cat)
+
+# Extract the tool name and command from the JSON input
+TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
+
+# Only intercept Bash commands
+if [[ "$TOOL_NAME" != "Bash" ]]; then
+    echo "$INPUT"
+    exit 0
+fi
+
+# Extract the command from the tool input
+COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // .tool_input // empty')
+
+if [[ -z "$COMMAND" ]]; then
+    echo "$INPUT"
+    exit 0
+fi
+
+# Normalize command: trim whitespace, collapse spaces
+NORMALIZED=$(echo "$COMMAND" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/[[:space:]]\+/ /g')
+
+# Get current project path
+PROJECT_PATH="${CLAUDE_PROJECT_DIR:-$(pwd)}"
+
+# Define destructive patterns (extended regex)
+declare -a DANGEROUS_PATTERNS=(
+    # rm -rf variants
+    '(^|[[:space:];|&`$({])rm[[:space:]]+(-[[:alnum:]]*r[[:alnum:]]*f[[:alnum:]]*|-rf[[:alnum:]]*|--recursive.*--force|--force.*--recursive)'
+    # DROP TABLE
+    '(^|[[:space:];|&`$({])DROP[[:space:]]+TABLE[[:space:]]+'
+    # TRUNCATE TABLE
+    '(^|[[:space:];|&`$({])TRUNCATE[[:space:]]+(TABLE[[:space:]]+)?'
+    # DELETE FROM without WHERE
+    '(^|[[:space:];|&`$({])DELETE[[:space:]]+FROM[[:space:]]+[^[:space:]]+[[:space:]]*;'
+    # git push --force variants
+    '(^|[[:space:];|&`$({])git[[:space:]]+push[[:space:]]+.*(--force|--force-with-lease|--delete|-f[[:space:]])'
+    # git push --force to main/master
+    '(^|[[:space:];|&`$({])git[[:space:]]+push[[:space:]]+.*(main|master).*(--force|--force-with-lease|-f)'
+    # Force push shorthand
+    '(^|[[:space:];|&`$({])git[[:space:]]+push[[:space:]]+(-f|--force)[[:space:]]'
+    # chmod 777 on system dirs
+    '(^|[[:space:];|&`$({])chmod[[:space:]]+.*777[[:space:]]+/(etc|usr|bin|lib|var|opt|root|home|tmp)'
+    # fork bomb
+    '(^|[[:space:];|&`$({])[^[:space:]]*\(\)[[:space:]]*\{[[:space:]]*[^}]*\|[^}]*&[[:space:]]*\}'
+    # dd destructive writes
+    '(^|[[:space:];|&`$({])dd[[:space:]]+.*of=/dev/(sd[a-z]+|hd[a-z]+|nvme[0-9]+)'
+)
+
+# Also check for DELETE FROM without WHERE (case-insensitive SQL check)
+DELETE_NO_WHERE=$(echo "$NORMALIZED" | grep -iE '(^|[[:space:];|&`$({])DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*;' || true)
+
+BLOCKED=false
+BLOCKED_REASON=""
+
+# Check each pattern
+for pattern in "${DANGEROUS_PATTERNS[@]}"; do
+    if echo "$NORMALIZED" | grep -iEq "$pattern"; then
+        BLOCKED=true
+        BLOCKED_REASON="Command matches dangerous pattern: $pattern"
+        break
+    fi
+done
+
+# Check DELETE without WHERE separately
+if [[ -n "$DELETE_NO_WHERE" ]] && [[ "$BLOCKED" == "false" ]]; then
+    # Verify there's no WHERE clause (case-insensitive)
+    if ! echo "$NORMALIZED" | grep -iq 'WHERE[[:space:]]'; then
+        BLOCKED=true
+        BLOCKED_REASON="DELETE FROM without WHERE clause detected"
+    fi
+fi
+
+if [[ "$BLOCKED" == "true" ]]; then
+    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
+    
+    # Log the blocked attempt
+    cat >> "$LOG_FILE" <<EOF
+[$TIMESTAMP] BLOCKED
+  Command: $COMMAND
+  Project: $PROJECT_PATH
+  Reason:  $BLOCKED_REASON
+---
+EOF
+
+    # Output a modified response that tells Claude the command was blocked
+    jq -n --arg reason "$BLOCKED_REASON" --arg cmd "$COMMAND" '{
+        "decision": "block",
+        "reason": "\($reason)",
+        "message": "⚠️  DESTRUCTIVE COMMAND BLOCKED\n\nThe following command was intercepted by the pre-tool-use security hook:\n\n  \($cmd)\n\nReason: \($reason)\n\nThis command could cause irreversible damage. If you are