#!/usr/bin/env bash
# Fast automated installer for Claude Code Pre-Tool-Use Destructive Command Blocker
set -euo pipefail

TARGET_DIR="$HOME/.claude/hooks"
HOOK_FILE="$TARGET_DIR/block_destructive_bash.py"

mkdir -p "$TARGET_DIR"

# Download or copy hook
if [ -f "$(dirname "$0")/block_destructive_bash.py" ]; then
  cp "$(dirname "$0")/block_destructive_bash.py" "$HOOK_FILE"
else
  curl -sSL "https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-bash/block_destructive_bash.py" -o "$HOOK_FILE"
fi

chmod +x "$HOOK_FILE"
touch "$TARGET_DIR/blocked.log"

echo "[SUCCESS] Destructive command blocker installed at: $HOOK_FILE"
echo "[INFO] Audit logs will be saved to: $TARGET_DIR/blocked.log"
