#!/usr/bin/env bash
# pre-tool-use hook for Claude Code
# Blocks destructive bash commands before execution

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('command',''))" 2>/dev/null)

LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Patterns to block
if [[ "$COMMAND" =~ rm\ +-rf ]] || \
   [[ "$COMMAND" =~ rm\ +-r[^a-z]*\ -f ]] || \
   [[ "$COMMAND" =~ git\ push\ .*--force ]] || \
   [[ "$COMMAND" =~ git\ push\ .*-f\  ]] || \
   [[ "$COMMAND" =~ DROP\ (TABLE|DATABASE) ]] || \
   [[ "$COMMAND" =~ ^TRUNCATE ]] || \
   [[ "$COMMAND" =~ DELETE\ FROM[[:space:]]+[^;]+\; ]] && ! [[ "$COMMAND" =~ WHERE ]] || \
   [[ "$COMMAND" =~ [[:space:]]\/dev\/ ]] || \
   [[ "$COMMAND" =~ mkfs\. ]] || \
   [[ "$COMMAND" =~ chmod\ -R\ 0[0-9][0-9] ]] || \
   [[ "$COMMAND" =~ :\(\)\{\ :\|:\&\ };: ]]
then
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | BLOCKED | $(pwd) | $COMMAND" >> "$LOG_FILE"
    echo '{"block": true, "message": "Blocked: destructive command detected (see ~/.claude/hooks/blocked.log)"}'
else
    echo '{"allow": true}'
fi
