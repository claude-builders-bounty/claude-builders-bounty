#!/usr/bin/env bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py
echo "✅ Safety hook installed successfully to ~/.claude/hooks/"
