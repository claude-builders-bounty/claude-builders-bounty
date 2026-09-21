#!/usr/bin/env bash
# Installation script for Claude Code block-destructive-bash hook
set -e

mkdir -p ~/.claude/hooks
cp "$(dirname "$0")/block_destructive.py" ~/.claude/hooks/block-destructive.py
chmod +x ~/.claude/hooks/block-destructive.py

echo "✅ Claude Code pre-tool-use hook installed to ~/.claude/hooks/block-destructive.py"
