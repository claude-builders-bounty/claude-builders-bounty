#!/bin/bash
# Claude Safety Hook - Quick Installation Script
# Usage: curl -sSL https://raw.githubusercontent.com/.../install.sh | bash

set -e

echo "🛡️  Installing Claude Safety Hook..."
echo ""

# Create hooks directory
mkdir -p ~/.claude/hooks

# Download the hook
if [ -f "pre_tool_use.py" ]; then
    # Local installation
    cp pre_tool_use.py ~/.claude/hooks/
else
    # Remote installation
    curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre_tool_use.py \
        -o ~/.claude/hooks/pre_tool_use.py
fi

# Make executable
chmod +x ~/.claude/hooks/pre_tool_use.py

# Create log directory
mkdir -p ~/.claude/hooks

# Test installation
if python3 ~/.claude/hooks/pre_tool_use.py <<< '{"tool_name":"bash","tool_input":{"command":"echo test"}}' 2>/dev/null; then
    echo "✅ Installation successful!"
    echo ""
    echo "📍 Hook location: ~/.claude/hooks/pre_tool_use.py"
    echo "📝 Log file: ~/.claude/hooks/blocked.log"
    echo ""
    echo "🧪 Testing with safe command: echo test"
    echo "   Result: ✅ Allowed"
    echo ""
    echo "🛡️  Claude is now protected from destructive commands!"
    echo ""
    echo "Try these commands to test the hook:"
    echo "  rm -rf /tmp/test"
    echo "  git push --force"
    echo ""
else
    echo "❌ Installation failed. Please check Python 3 is installed."
    exit 1
fi
