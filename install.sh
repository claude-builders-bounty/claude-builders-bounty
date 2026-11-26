#!/bin/sh
# Install the destructive-command PreToolUse hook (1 command: ./install.sh).
# Copies the hook to ~/.claude/hooks/, makes it executable, and registers
# it in ~/.claude/settings.json (merging with any existing settings).
set -eu
HOOK_SRC="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/hooks/block-destructive-commands.py"
HOOK_DST="$HOME/.claude/hooks/block-destructive-commands.py"
mkdir -p "$HOME/.claude/hooks"
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
python3 - "$HOOK_DST" <<'PYEOF'
import json, sys
from pathlib import Path
hook = sys.argv[1]
settings_path = Path.home() / ".claude" / "settings.json"
settings = {}
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError:
        settings = {}
hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": hook}]}
if entry not in pre:
    pre.append(entry)
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
print(f"Registered PreToolUse hook in {settings_path}")
PYEOF
echo "Installed: $HOOK_DST"
echo "Blocked attempts will be logged to ~/.claude/hooks/blocked.log"
