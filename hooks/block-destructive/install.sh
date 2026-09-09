#!/usr/bin/env bash
# Install the block-destructive PreToolUse hook for Claude Code.
# Usage: bash install.sh   (one command)
set -euo pipefail

HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$HOOKS_DIR"
cp "$(dirname "$0")/pre-tool-use.py" "$HOOKS_DIR/pre-tool-use.py"
chmod +x "$HOOKS_DIR/pre-tool-use.py"

# Register the hook in settings.json without clobbering existing config.
python3 - "$SETTINGS" <<'PY'
import json, sys, os
path = sys.argv[1]
settings = {}
if os.path.exists(path):
    try:
        with open(path, encoding="utf-8") as f:
            settings = json.load(f)
    except ValueError:
        settings = {}
hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": f"python3 {os.path.expanduser('~/.claude/hooks/pre-tool-use.py')}"}],
}
if entry not in pre:
    pre.append(entry)
with open(path, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
PY

echo "✅ Installed. Blocked attempts will be logged to $HOOKS_DIR/blocked.log"
