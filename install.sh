#!/usr/bin/env bash
# Install the destructive command guard hook for Claude Code.
# Usage: git clone <repo> && cd <repo> && bash install.sh
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$SCRIPT_DIR/hooks/block-destructive.py"

if [ ! -f "$SOURCE" ]; then
    echo "Error: hooks/block-destructive.py not found. Run this from the repo root." >&2
    exit 1
fi

# Step 1: Copy hook script
mkdir -p "$HOOK_DIR"
cp "$SOURCE" "$HOOK_DIR/block-destructive.py"
chmod +x "$HOOK_DIR/block-destructive.py"
echo "Copied hook to $HOOK_DIR/block-destructive.py"

# Step 2: Register in ~/.claude/settings.json (idempotent)
python3 << 'PYEOF'
import json
import os

settings_path = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(settings_path), exist_ok=True)

if os.path.exists(settings_path):
    with open(settings_path) as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError:
            settings = {}
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

hook_command = "python3 ~/.claude/hooks/block-destructive.py"

# Check if already registered to avoid duplicates
already_exists = any(
    any(h.get("command") == hook_command for h in entry.get("hooks", []))
    for entry in pre_tool_use
)

if not already_exists:
    pre_tool_use.append({
        "matcher": "Bash",
        "hooks": [{
            "type": "command",
            "command": hook_command
        }]
    })
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print("Registered hook in " + settings_path)
else:
    print("Hook already registered in " + settings_path)
PYEOF

echo ""
echo "Destructive command guard installed!"
echo "  Hook:   $HOOK_DIR/block-destructive.py"
echo "  Logs:   $HOOK_DIR/blocked.log"
echo "  Config: $HOME/.claude/settings.json"
