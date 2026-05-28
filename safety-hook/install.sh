#!/usr/bin/env bash
# install.sh — One-command installer for the safety hook
# Usage: curl -fsSL <raw-url>/install.sh | bash

set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
HOOK_FILE="${HOOK_DIR}/safety-hook.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🛡️  Installing Claude Code Safety Hook..."

# Create hooks directory
mkdir -p "$HOOK_DIR"

# Copy the hook
cp "${SCRIPT_DIR}/safety-hook.sh" "$HOOK_FILE"
chmod +x "$HOOK_FILE"

echo "✅ Safety hook installed to: ${HOOK_FILE}"
echo ""
echo "The hook will now intercept dangerous commands in Claude Code."
echo "Blocked attempts are logged to: ${HOOK_DIR}/blocked.log"
echo ""
echo "To uninstall: rm ${HOOK_FILE}"
