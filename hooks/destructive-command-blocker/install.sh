#!/usr/bin/env bash
set -e

HOOKS_DIR="$HOME/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🛡️ Installing Claude Code Destructive Command Blocker..."

mkdir -p "$HOOKS_DIR"
cp "$SCRIPT_DIR/pre_tool_use.py" "$HOOKS_DIR/pre_tool_use.py"
chmod +x "$HOOKS_DIR/pre_tool_use.py"

# Create pre-tool-use entrypoint executable
cat << 'EOF' > "$HOOKS_DIR/pre-tool-use"
#!/usr/bin/env bash
python3 "$HOME/.claude/hooks/pre_tool_use.py" "$@"
EOF
chmod +x "$HOOKS_DIR/pre-tool-use"

# Touch blocked log file with proper permissions
touch "$HOOKS_DIR/blocked.log"

echo "✅ Successfully installed! Dangerous commands will now be blocked and logged to ~/.claude/hooks/blocked.log"
