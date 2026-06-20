#!/usr/bin/env bash
set -eo pipefail

# Pre-tool-use hook that blocks destructive bash commands
# Place in ~/.claude/hooks/ and configure in ~/.claude/settings.json

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

INPUT=$(cat)

TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Only check Bash tool calls
if [[ "$TOOL" != "Bash" ]]; then
  exit 0
fi

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if [[ -z "$CMD" ]]; then
  exit 0
fi

PROJECT_PATH=$(echo "$INPUT" | jq -r '.tool_input.working_directory // empty')
if [[ -z "$PROJECT_PATH" ]]; then
  PROJECT_PATH=$(pwd)
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Patterns to block (case-insensitive)
DENY_PATTERNS=(
  'rm\s+-[a-z]*r[a-z]*f[a-z]*\s+/'          # rm -rf /
  'rm\s+-[a-z]*f[a-z]*r[a-z]*\s+/'          # rm -fr /
  'rm\s+-rf\s+~'                              # rm -rf ~
  'rm\s+-rf\s+\*'                             # rm -rf *
  'rm\s+-rf\s+\.'                             # rm -rf .
  'rm\s+-rf\s+/'                              # rm -rf /
  'DROP\s+TABLE'                              # DROP TABLE
  'DROP\s+DATABASE'                           # DROP DATABASE
  'TRUNCATE'                                  # TRUNCATE
  'DELETE\s+FROM\s+\w+\s*;?$'                # DELETE FROM without WHERE
  'DELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1' # DELETE FROM WHERE 1=1
  'git\s+push\s+.*--force\s'                 # git push --force
  'git\s+reset\s+--hard'                      # git reset --hard
  'git\s+clean\s+-f'                          # git clean -f
  'sudo\s+rm'                                 # sudo rm
  'chmod\s+-R\s+777'                          # chmod -R 777
  'curl.*\|\s*bash'                           # curl | bash
  'wget.*\|\s*bash'                           # wget | bash
  ':\(\)\{\s*:\|:\s*&\s*\};:'               # fork bomb
)

BLOCKED=false
MATCHED_PATTERN=""

for pat in "${DENY_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qEi "$pat"; then
    BLOCKED=true
    MATCHED_PATTERN="$pat"
    break
  fi
done

# Special handling for git push --force: allow --force-with-lease
if [[ "$BLOCKED" == "true" && "$MATCHED_PATTERN" == 'git\s+push\s+.*--force\s' ]]; then
  if echo "$CMD" | grep -qEi 'git\s+push\s+.*--force-with-lease'; then
    BLOCKED=false
    MATCHED_PATTERN=""
  fi
fi

if [[ "$BLOCKED" == "true" ]]; then
  # Log the blocked attempt
  echo "[$TIMESTAMP] BLOCKED | pattern: $MATCHED_PATTERN | command: $CMD | project: $PROJECT_PATH" >> "$LOG_FILE"

  # Return block decision with explanation
  cat <<EOF
{"decision":"block","reason":"This command was blocked by the destructive-command-blocker hook. Matched pattern: $MATCHED_PATTERN\n\nCommand: $CMD\n\nThis command could cause irreversible damage. Use a safer alternative or explain why it's necessary."}
EOF
  exit 0
fi

exit 0
