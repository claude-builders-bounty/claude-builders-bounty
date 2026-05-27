#!/usr/bin/env bash
set -euo pipefail

HOOK_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.claude/hooks/destructive-command-guard.py"
HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$HOOK_SOURCE" "$HOOK_DIR/destructive-command-guard.py"
chmod +x "$HOOK_DIR/destructive-command-guard.py"

python3 - "$SETTINGS_FILE" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1]).expanduser()
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"{settings_path} is not valid JSON; fix it before installing this hook")
else:
    settings = {}

hook_group = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive-command-guard.py",
        }
    ],
}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

already_installed = any(
    group.get("matcher") == "Bash"
    and any(
        hook.get("command") == "python3 ~/.claude/hooks/destructive-command-guard.py"
        for hook in group.get("hooks", [])
    )
    for group in pre_tool_use
)

if not already_installed:
    pre_tool_use.append(hook_group)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive-command-guard.py into $HOOK_DIR"
echo "Updated $SETTINGS_FILE"
