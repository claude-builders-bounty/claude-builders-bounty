#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SOURCE="$SCRIPT_DIR/hooks/block-dangerous-bash.py"
CLAUDE_CONFIG_HOME="${CLAUDE_CONFIG_HOME:-$HOME/.claude}"
HOOK_DIR="$CLAUDE_CONFIG_HOME/hooks"
HOOK_TARGET="$HOOK_DIR/block-dangerous-bash.py"
SETTINGS_PATH="$CLAUDE_CONFIG_HOME/settings.json"

mkdir -p "$HOOK_DIR"
cp "$HOOK_SOURCE" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

SETTINGS_PATH="$SETTINGS_PATH" HOOK_TARGET="$HOOK_TARGET" python3 - <<'PY'
import json
import os
from pathlib import Path

settings_path = Path(os.environ["SETTINGS_PATH"])
hook_target = Path(os.environ["HOOK_TARGET"])
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text(encoding="utf-8").strip():
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
command = f"python3 {hook_target}"
entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": command}],
}

def same_entry(candidate):
    if not isinstance(candidate, dict):
        return False
    if candidate.get("matcher") != "Bash":
        return False
    for hook in candidate.get("hooks", []):
        if isinstance(hook, dict) and hook.get("command") == command:
            return True
    return False

if not any(same_entry(candidate) for candidate in pre_tool_use):
    pre_tool_use.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive command guard hook:"
echo "  $HOOK_TARGET"
echo "Updated Claude Code settings:"
echo "  $SETTINGS_PATH"
