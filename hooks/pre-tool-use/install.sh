#!/usr/bin/env bash
# Install script for the destructive-command-blocker hook
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks/pre-tool-use"
CONFIG_FILE="${HOME}/.claude/hooks/config.json"

echo "🔧 Installing destructive-command-blocker hook..."

# Create directories
mkdir -p "${HOOK_DIR}"

# Copy the hook script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "${SCRIPT_DIR}/block_destructive.py" "${HOOK_DIR}/"
chmod +x "${HOOK_DIR}/block_destructive.py"

echo "✅ Hook installed to ${HOOK_DIR}/block_destructive.py"

# Check if config exists
if [ -f "${CONFIG_FILE}" ]; then
    echo "⚠️  Config file already exists at ${CONFIG_FILE}"
    echo "   Manually add the Bash pre-tool-use hook entry from README.md"
else
    # Create default config
    cat > "${CONFIG_FILE}" << 'EOF'
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use/block_destructive.py"
          }
        ]
      }
    ]
  }
}
EOF
    echo "✅ Default config created at ${CONFIG_FILE}"
fi

echo ""
echo "🎉 Installation complete!"
echo "   The hook will now block destructive bash commands in Claude Code."
echo "   View blocked attempts: cat ~/.claude/hooks/blocked.log"
