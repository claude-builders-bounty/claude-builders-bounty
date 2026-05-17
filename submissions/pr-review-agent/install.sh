#!/bin/bash
# Installation script for Claude PR Review Agent

set -e

INSTALL_DIR="/usr/local/bin"
SCRIPT_NAME="claude-review"

echo "🔧 Installing Claude PR Review Agent..."

# Check for required dependencies
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install requests --quiet

# Copy script to install directory
if [ -w "$INSTALL_DIR" ]; then
    cp claude-review "$INSTALL_DIR/$SCRIPT_NAME"
    chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
else
    echo "⚠️  Need sudo access to install to $INSTALL_DIR"
    sudo cp claude-review "$INSTALL_DIR/$SCRIPT_NAME"
    sudo chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
fi

echo "✅ Installed to $INSTALL_DIR/$SCRIPT_NAME"

# Check for API keys
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
    echo "   Set it with: export ANTHROPIC_API_KEY='your-key'"
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo ""
    echo "⚠️  Warning: GITHUB_TOKEN not set"
    echo "   Set it with: export GITHUB_TOKEN='your-token'"
    echo "   (Required for private repos and posting comments)"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Usage:"
echo "  claude-review --pr https://github.com/owner/repo/pull/123"
echo "  claude-review --pr https://github.com/owner/repo/pull/123 --post"
echo ""
