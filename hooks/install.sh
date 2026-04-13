#!/usr/bin/env bash
# Install the pre-tool-use security hook for Claude Code
# Usage: bash hooks/install.sh

set -euo pipefail

HOOKS_DIR="$HOME/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "📦 Installing Claude Code security hook..."

# Create hooks directory
mkdir -p "$HOOKS_DIR"

# Copy the hook script
cp "$SCRIPT_DIR/pre-tool-use.py" "$HOOKS_DIR/pre-tool-use.py"
chmod +x "$HOOKS_DIR/pre-tool-use.py"

# Create empty log file
touch "$HOOKS_DIR/blocked.log"

echo "✅ Hook installed to $HOOKS_DIR/pre-tool-use.py"
echo "📝 Blocked commands will be logged to $HOOKS_DIR/blocked.log"
echo ""
echo "To uninstall, run: rm $HOOKS_DIR/pre-tool-use.py"
