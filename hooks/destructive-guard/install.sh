#!/usr/bin/env bash
set -e

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp pre_tool_use.py "$HOOK_DIR/pre_tool_use.py"
chmod +x "$HOOK_DIR/pre_tool_use.py"

python3 - <<'EOF'
import json, os, sys

path = os.path.expanduser("~/.claude/settings.json")
settings = {}
if os.path.exists(path):
    with open(path) as f:
        settings = json.load(f)

hook_entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py"}]
}

pre = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
# avoid duplicates
if not any(h.get("matcher") == "Bash" and
           any("pre_tool_use.py" in h2.get("command","") for h2 in h.get("hooks",[]))
           for h in pre):
    pre.append(hook_entry)

with open(path, "w") as f:
    json.dump(settings, f, indent=2)

print("✅ Hook installed. Restart Claude Code to activate.")
EOF
