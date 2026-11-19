#!/usr/bin/env bash
set -e

mkdir -p ~/.claude/hooks
cp "$(dirname "$0")/pre-tool-use.py" ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
echo "Security hook installed successfully to ~/.claude/hooks/pre-tool-use.py"
