#!/usr/bin/env bash
set -e

mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use

echo "✅ Claude Code pre-tool-use hook installed in ~/.claude/hooks/pre-tool-use"
