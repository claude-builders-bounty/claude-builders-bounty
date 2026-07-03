#!/usr/bin/env bash
# One-command install for destructive bash hook (bounty #3).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.claude/hooks
cp "$DIR/block_destructive.py" ~/.claude/hooks/block_destructive.py
chmod +x "$DIR/block_destructive.py" 2>/dev/null || true
echo "Installed block_destructive.py → ~/.claude/hooks/"
echo "Add hooks/settings.sample.json snippet to ~/.claude/settings.json (see hooks/README.md)"
