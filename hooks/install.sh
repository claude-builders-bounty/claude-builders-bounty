#!/bin/bash
# Installation script for Claude Code Destructive Command Blocker Hook

set -e

HOOK_URL="https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use-blocker.py"
HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="$HOOK_DIR/pre-tool-use"

echo "🔒 Installing Claude Code Destructive Command Blocker Hook..."

# Create hooks directory
mkdir -p "$HOOK_DIR"

# Download the hook
echo "📥 Downloading hook script..."
curl -fsSL "$HOOK_URL" > "$HOOK_FILE"

# Make it executable
chmod +x "$HOOK_FILE"

# Verify Python is available
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Warning: Python 3 not found. The hook requires Python 3.6+."
    echo "   Please install Python 3 and try again."
    exit 1
fi

# Test the hook
echo "🧪 Testing hook..."
echo '{"tool": "bash", "input": {"command": "echo test"}, "project_path": "/tmp"}' | python3 "$HOOK_FILE" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Hook installed successfully!"
    echo ""
    echo "📍 Location: $HOOK_FILE"
    echo "📋 Logs will be saved to: $HOOK_DIR/blocked.log"
    echo ""
    echo "The hook is now active and will block dangerous commands."
    echo "Try running 'rm -rf /tmp/test' in Claude Code to see it in action."
else
    echo "❌ Hook test failed. Please check the installation."
    exit 1
fi
