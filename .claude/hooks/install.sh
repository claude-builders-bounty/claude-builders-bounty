#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/.claude/hooks"
cp ".claude/hooks/block_destructive_bash.py" "$HOME/.claude/hooks/block_destructive_bash.py"
chmod +x "$HOME/.claude/hooks/block_destructive_bash.py"

python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        settings = {}
else:
    settings = {}

hook = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py",
        }
    ],
}

pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
if hook not in pre_tool_use:
    pre_tool_use.append(hook)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed destructive Bash guard in {settings_path}")
PY
