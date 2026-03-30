#!/bin/bash
# Pre-tool-use hook: blocks destructive bash commands
# Claude Code hooks format: https://docs.anthropic.com/claude-code/hooks

HOOK_LOG="$HOME/.claude/hooks/blocked.log"
TOOL_NAME="$1"
TOOL_INPUT="$2"

# Blocked patterns
BLOCKED_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf --"
  "DROP TABLE"
  "TRUNCATE TABLE"
  "git push --force"
  "git push -f"
  "DELETE FROM [a-zA-Z_]+;$"
  "DELETE FROM [a-zA-Z_]+ [^w]"
  "ALTER TABLE.*DROP"
  "sudo rm"
  "chmod -R 777 /"
  "mkfs\."
  ":(){ :|:& };:"
  "dd if=/dev/zero of=/dev/"
  "wget.*\| sh"
  "curl.*\| sh"
)

is_blocked() {
  local cmd="$1"
  for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$cmd" | grep -qiE "$pattern"; then
      return 0
    fi
  done
  return 1
}

if [[ "$TOOL_NAME" == "Bash" ]] || [[ "$TOOL_NAME" == "Read" && -n "$TOOL_INPUT" ]]; then
  # Extract command from tool input
  CMD=$(echo "$TOOL_INPUT" | grep -oE '`[^`]+`' | head -1 | sed 's/`//g')
  [[ -z "$CMD" ]] && CMD="$TOOL_INPUT"
  
  if is_blocked "$CMD"; then
    # Log blocked attempt
    mkdir -p "$(dirname "$HOOK_LOG")"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED: $CMD | Project: ${PROJECT_PATH:-unknown}" >> "$HOOK_LOG"
    
    echo ""
    echo "=========================================="
    echo "HOOK: COMMAND BLOCKED"
    echo "=========================================="
    echo ""
    echo "This command was blocked by the safety hook:"
    echo ""
    echo "  $CMD"
    echo ""
    echo "Reason: Matches a destructive or dangerous pattern."
    echo ""
    echo "If this is a legitimate command, you can:"
    echo "  1. Ask the user to confirm the action"
    echo "  2. Run the command outside of Claude Code"
    echo ""
    echo "Logged to: $HOOK_LOG"
    echo "=========================================="
    echo ""
    
    exit 1
  fi
fi

# Block specific Bash patterns directly
if [[ "$TOOL_NAME" == "Bash" ]]; then
  if echo "$TOOL_INPUT" | grep -qiE "rm -rf|DROP TABLE|TRUNCATE|DELETE FROM.*[^wW ]$|git push --force|git push -f"; then
    mkdir -p "$(dirname "$HOOK_LOG")"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED: $TOOL_INPUT | Project: ${PROJECT_PATH:-unknown}" >> "$HOOK_LOG"
    
    echo ""
    echo "=========================================="
    echo "HOOK: COMMAND BLOCKED - Destructive Pattern Detected"
    echo "=========================================="
    echo ""
    echo "Blocked command: $TOOL_INPUT"
    echo ""
    echo "This pattern is blocked:"
    echo "  - rm -rf (recursive delete)"
    echo "  - DROP/TRUNCATE TABLE (database destruction)"
    echo "  - DELETE without WHERE (data loss)"
    echo "  - git push --force (history rewrite)"
    echo ""
    echo "Contact the repository owner if this is needed."
    echo "=========================================="
    exit 1
  fi
fi

exit 0
