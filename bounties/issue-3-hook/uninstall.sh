#!/usr/bin/env bash
# uninstall.sh — Remove the anti-destructive hook from Claude Code
set -euo pipefail

HOOK_DST="$HOME/.claude/hooks/anti-destructive.py"
SETTINGS="$HOME/.claude/settings.json"

echo "🗑️  Uninstalling anti-destructive hook..."

# Remove hook script
if [ -f "$HOOK_DST" ]; then
    rm "$HOOK_DST"
    echo "   ✓ Removed $HOOK_DST"
fi

# Remove from settings.json
if [ -f "$SETTINGS" ]; then
    python3 - <<PYEOF
import json, os

settings_path = os.path.expanduser("~/.claude/settings.json")
with open(settings_path, "r") as f:
    settings = json.load(f)

pre = settings.get("hooks", {}).get("PreToolUse", [])
settings["hooks"]["PreToolUse"] = [
    g for g in pre
    if not any("anti-destructive" in str(h.get("command","")) for h in g.get("hooks",[]))
]

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
print("   ✓ Hook removed from settings.json")
PYEOF
fi

echo "✅ Uninstalled."
