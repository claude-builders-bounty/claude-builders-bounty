#!/bin/bash
# Install script for claude-review

echo "Installing claude-review..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make script executable
chmod +x claude_review.py

echo ""
echo "✅ Installation complete!"
echo ""
echo "To use claude-review:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Set your API key: export ANTHROPIC_API_KEY='your-key-here'"
echo "  3. Run: python claude_review.py --pr https://github.com/owner/repo/pull/123"
echo ""
