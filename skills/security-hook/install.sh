#!/bin/bash
# Install the security hook

set -e

HOOKS_DIR="$HOME/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing pre-tool-use security hook..."

# Create hooks directory
mkdir -p "$HOOKS_DIR"

# Copy hook
cp "$SCRIPT_DIR/pre-tool-use.sh" "$HOOKS_DIR/"

# Make executable
chmod +x "$HOOKS_DIR/pre-tool-use.sh"

# Create log file
touch "$HOOKS_DIR/blocked.log"

echo "✓ Installed to $HOOKS_DIR/pre-tool-use.sh"
echo "✓ Log file: $HOOKS_DIR/blocked.log"
echo ""
echo "Usage: The hook will automatically block destructive commands."
echo "View blocked attempts: cat $HOOKS_DIR/blocked.log"