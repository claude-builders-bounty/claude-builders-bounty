#!/usr/bin/env bash
# Install the Destructive Command Guard hook for Claude Code.
# Usage: bash install.sh

set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks/pre-tool-use"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$HOOK_DIR"
cp "$SCRIPT_DIR/guard.py" "$HOOK_DIR/guard.py"
chmod +x "$HOOK_DIR/guard.py"

echo "✅ Destructive Command Guard installed to $HOOK_DIR/guard.py"
echo "   Blocked attempts will be logged to ~/.claude/hooks/blocked.log"
