#!/bin/bash
set -e

# Make hook executable locally
chmod +x pre-tool-use.py

# Create the hook directory
mkdir -p ~/.claude/hooks

# Copy and rename script to pre-tool-use in the hooks directory
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use

echo "Destructive command blocker hook installed successfully to ~/.claude/hooks/pre-tool-use"
