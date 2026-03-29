#!/usr/bin/env bash
# install.sh — One-command installer for the Claude Code guard hook
#
# Usage:
#   bash install.sh          # Install globally
#   bash install.sh --remove # Uninstall

set -euo pipefail

HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARD_SRC="$SCRIPT_DIR/guard.sh"
GUARD_DST="$HOOKS_DIR/guard.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
if [[ "${1:-}" == "--remove" ]]; then
  echo -e "${YELLOW}Removing guard hook...${NC}"

  # Remove guard.sh
  if [[ -f "$GUARD_DST" ]]; then
    rm "$GUARD_DST"
    echo -e "${GREEN}Removed $GUARD_DST${NC}"
  fi

  # Remove hook entry from settings.json
  if [[ -f "$SETTINGS_FILE" ]] && command -v jq &>/dev/null; then
    # Remove PreToolUse entries that reference guard.sh
    UPDATED=$(jq '
      if .hooks.PreToolUse then
        .hooks.PreToolUse |= map(
          .hooks |= map(select(.command | test("guard\\.sh") | not))
        ) |
        .hooks.PreToolUse |= map(select(.hooks | length > 0)) |
        if (.hooks.PreToolUse | length) == 0 then del(.hooks.PreToolUse) else . end |
        if (.hooks | length) == 0 then del(.hooks) else . end
      else . end
    ' "$SETTINGS_FILE")
    echo "$UPDATED" > "$SETTINGS_FILE"
    echo -e "${GREEN}Removed hook config from $SETTINGS_FILE${NC}"
  fi

  echo -e "${GREEN}Guard hook uninstalled.${NC}"
  exit 0
fi

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
echo -e "${GREEN}Installing Claude Code guard hook...${NC}"

# Check for jq
if ! command -v jq &>/dev/null; then
  echo -e "${RED}Error: jq is required but not installed.${NC}"
  echo "Install it with: sudo apt install jq  OR  brew install jq"
  exit 1
fi

# 1. Copy guard.sh
mkdir -p "$HOOKS_DIR"
cp "$GUARD_SRC" "$GUARD_DST"
chmod +x "$GUARD_DST"
echo -e "  Copied guard.sh to ${GREEN}$GUARD_DST${NC}"

# 2. Merge hook config into settings.json
HOOK_ENTRY='{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "'"$GUARD_DST"'",
      "timeout": 10
    }
  ]
}'

if [[ ! -f "$SETTINGS_FILE" ]]; then
  # Create settings.json from scratch
  echo "{}" > "$SETTINGS_FILE"
fi

# Check if guard.sh is already configured
if jq -e '.hooks.PreToolUse[]?.hooks[]? | select(.command | test("guard\\.sh"))' "$SETTINGS_FILE" &>/dev/null; then
  echo -e "  ${YELLOW}Hook already configured in settings.json — skipping${NC}"
else
  # Merge: add our entry to PreToolUse array (create if absent)
  UPDATED=$(jq --argjson entry "$HOOK_ENTRY" '
    .hooks //= {} |
    .hooks.PreToolUse //= [] |
    .hooks.PreToolUse += [$entry]
  ' "$SETTINGS_FILE")
  echo "$UPDATED" > "$SETTINGS_FILE"
  echo -e "  Added hook config to ${GREEN}$SETTINGS_FILE${NC}"
fi

# 3. Create example custom patterns file if it doesn't exist
PATTERNS_FILE="$HOOKS_DIR/guard-patterns.txt"
if [[ ! -f "$PATTERNS_FILE" ]]; then
  cat > "$PATTERNS_FILE" << 'PATTERNS'
# Custom guard patterns — one extended regex per line
# Lines starting with # are comments, empty lines are ignored
#
# Examples (uncomment to enable):
# chmod\s+777           # Block world-writable permissions
# mkfs\.                # Block filesystem formatting
# dd\s+if=              # Block raw disk writes
# >\s*/dev/sd           # Block writing to raw devices
# curl.*\|\s*sh         # Block pipe-to-shell installs
PATTERNS
  echo -e "  Created example patterns file at ${GREEN}$PATTERNS_FILE${NC}"
fi

echo ""
echo -e "${GREEN}Installation complete.${NC}"
echo ""
echo "The guard hook will now block dangerous commands like:"
echo "  - rm -rf            (recursive force delete)"
echo "  - DROP TABLE        (database table deletion)"
echo "  - git push --force  (force push)"
echo "  - TRUNCATE          (table truncation)"
echo "  - DELETE FROM        (without WHERE clause)"
echo ""
echo "Blocked attempts are logged to: $HOOKS_DIR/blocked.log"
echo "Add custom patterns to: $PATTERNS_FILE"
echo ""
echo "To uninstall: bash install.sh --remove"
