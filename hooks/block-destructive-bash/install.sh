#!/usr/bin/env bash
set -euo pipefail

HOOKS_DIR="$HOME/.claude/hooks"
HOOK_URL="https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-bash/pre-tool-use.py"

mkdir -p "$HOOKS_DIR"

if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$HOOK_URL" -o "$HOOKS_DIR/pre-tool-use"
else
    wget -q "$HOOK_URL" -O "$HOOKS_DIR/pre-tool-use"
fi

chmod +x "$HOOKS_DIR/pre-tool-use"
echo "✅ Hook installed to $HOOKS_DIR/pre-tool-use"