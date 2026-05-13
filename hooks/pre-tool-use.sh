#!/usr/bin/env bash
# pre-tool-use.sh — Claude Code pre-tool-use hook
# Blocks dangerous bash commands and logs attempts
# Install: ln -sf "$PWD/hooks/pre-tool-use.sh" ~/.claude/hooks/pre-tool-use

set -euo pipefail

HOOK_LOG="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$HOOK_LOG")"

# Read the command from stdin or first argument
COMMAND="${1:-$(cat)}"

# Dangerous patterns (case-insensitive)
PATTERNS=(
  "rm[[:space:]]+-rf[[:space:]]+/"
  "rm[[:space:]]+-rf[[:space:]]+~"
  "rm[[:space:]]+-rf[[:space:]]+.*--no-preserve-root"
  "DROP[[:space:]]+TABLE"
  "DROP[[:space:]]+DATABASE"
  "TRUNCATE[[:space:]]+TABLE"
  "TRUNCATE[[:space:]]+[a-z_]+[[:space:]]*;"
  "DELETE[[:space:]]+FROM[[:space:]]+[a-z_]+[[:space:]]*(?!.*WHERE)"
  "git[[:space:]]+push[[:space:]]+--force"
  "git[[:space:]]+push[[:space:]]+-f[[:space:]]+.*--force"
  ":[[:space:]]*![[:space:]]*rm[[:space:]]+rf"
)

for pattern in "${PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    TIMESTAMP=$(date -Iseconds)
    PROJECT_PATH="${PWD}"
    echo "[$TIMESTAMP] BLOCKED | cmd: $COMMAND | path: $PROJECT_PATH" >> "$HOOK_LOG"
    
    cat <<-EOF
	
	⛔ **Command Blocked by Safety Hook**
	
	The following command was intercepted and blocked:
	
	\`\`\`
	$COMMAND
	\`\`\`
	
	**Reason**: Matched dangerous pattern: \`$pattern\`
	
	If you are absolutely sure you want to run this command, use:
	\`\`\`bash
	# Disable hook temporarily
	export CLAUDE_SAFETY_BYPASS=true
	# Then run your command
	$COMMAND
	\`\`\`
	
	EOF
    exit 1
  fi
done

# Pass through if safe
echo "$COMMAND"
exit 0
