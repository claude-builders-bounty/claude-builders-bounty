#!/bin/bash
# Installation script for Claude Safety Hook

set -e

HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="$HOOK_DIR/pre-tool-use"

echo "🔧 Installing Claude Safety Hook..."

# Create hooks directory
mkdir -p "$HOOK_DIR"
echo "✓ Created directory: $HOOK_DIR"

# Copy hook file
cp safety_hook.py "$HOOK_FILE"
echo "✓ Installed hook: $HOOK_FILE"

# Make executable
chmod +x "$HOOK_FILE"
echo "✓ Made hook executable"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "The hook will now block dangerous bash commands."
echo "Blocked attempts are logged to: $HOOK_DIR/blocked.log"
echo ""
echo "Test with: rm -rf / (will be blocked)"
