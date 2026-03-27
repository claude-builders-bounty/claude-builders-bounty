#!/bin/bash
#
# CHANGELOG Generator Wrapper Script
# Usage: ./changelog.sh [VERSION] [FROM_TAG]
#
# Examples:
#   ./changelog.sh                    # Generate from last tag
#   ./changelog.sh 1.2.0              # Generate for version 1.2.0
#   ./changelog.sh 1.2.0 v1.1.0       # Generate from tag v1.1.0
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/generate_changelog.py"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if in a git repo
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo "❌ Not a git repository."
    exit 1
fi

# Parse arguments
VERSION="${1:-Unreleased}"
FROM_TAG="${2:-}"

# Build command
CMD="python3 \"$PYTHON_SCRIPT\" --version \"$VERSION\""

if [ -n "$FROM_TAG" ]; then
    CMD="$CMD --from-tag \"$FROM_TAG\""
fi

# Run
echo "🚀 Generating CHANGELOG..."
eval $CMD

echo ""
echo "✅ Done! Check CHANGELOG.md"