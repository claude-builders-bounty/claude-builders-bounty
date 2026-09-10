#!/usr/bin/env bash
set -e

HOOK_DIR="$HOME/.claude/hooks"
HOOK_PATH="$HOOK_DIR/block_destructive_bash.py"
SETTINGS_PATH="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp block_destructive_bash.py "$HOOK_PATH"
chmod +x "$HOOK_PATH"

python3 - "$SETTINGS_PATH" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot update {settings_path}: invalid JSON: {exc}")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
if not isinstance(hooks, dict):
    raise SystemExit("Cannot update settings: 'hooks' must be an object.")

pre = hooks.setdefault("PreToolUse", [])
if not isinstance(pre, list):
    raise SystemExit("Cannot update settings: 'PreToolUse' must be a list.")

entry = {
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
    }]
}

already = any(
    isinstance(item, dict)
    and item.get("matcher") == "Bash"
    and any(
        isinstance(h, dict)
        and h.get("type") == "command"
        and h.get("command") == entry["hooks"][0]["command"]
        for h in item.get("hooks", [])
    )
    for item in pre
)

if not already:
    pre.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n")
print(f"Settings updated: {settings_path}")
PY

echo "Hook installed: $HOOK_PATH"
echo "Claude Code PreToolUse hook configured."
