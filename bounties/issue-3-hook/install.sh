#!/usr/bin/env bash
# install.sh — Anti-destructive hook installer for Claude Code
# Usage: bash install.sh
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook.py"
HOOK_DST="$HOOK_DIR/anti-destructive.py"
SETTINGS="$HOME/.claude/settings.json"

echo "🔧 Installing Claude Code anti-destructive hook..."

# ── 1. Copy hook script ────────────────────────────────────────────────────────
mkdir -p "$HOOK_DIR"
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
echo "   ✓ Hook copied to $HOOK_DST"

# ── 2. Register in ~/.claude/settings.json ─────────────────────────────────────
python3 - <<PYEOF
import json, os, sys

settings_path = os.path.expanduser("~/.claude/settings.json")
hook_dst = os.path.expanduser("~/.claude/hooks/anti-destructive.py")

# Load existing settings (or start fresh)
if os.path.exists(settings_path):
    with open(settings_path, "r") as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError:
            settings = {}
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

hook_entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": f"python3 {hook_dst}"
        }
    ]
}

# Avoid duplicates: remove any existing anti-destructive entries
pre_tool_use[:] = [
    g for g in pre_tool_use
    if not any("anti-destructive" in str(h.get("command","")) for h in g.get("hooks",[]))
]

pre_tool_use.append(hook_entry)

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

print(f"   ✓ Hook registered in {settings_path}")
PYEOF

echo ""
echo "✅ Done! The anti-destructive hook is active."
echo ""
echo "   Blocked patterns:"
echo "     • rm -rf"
echo "     • DROP TABLE"
echo "     • git push --force / -f"
echo "     • TRUNCATE"
echo "     • DELETE FROM without WHERE"
echo ""
echo "   Blocked attempts are logged to: ~/.claude/hooks/blocked.log"
echo ""
echo "   To uninstall: bash uninstall.sh"
