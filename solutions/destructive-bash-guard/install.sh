#!/bin/bash
set -e

# Create hook directory
mkdir -p ~/.claude/hooks

# Download hook file
echo "Downloading pre-tool-use.py hook..."
curl -sL -o ~/.claude/hooks/pre-tool-use.py https://raw.githubusercontent.com/namdamdoi68-oss/claude-builders-bounty/main/solutions/destructive-bash-guard/pre-tool-use.py

# Make executable
chmod +x ~/.claude/hooks/pre-tool-use.py

echo "Installation complete!"
