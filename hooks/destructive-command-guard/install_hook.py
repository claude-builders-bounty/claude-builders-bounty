#!/usr/bin/env python3
"""Install the destructive command guard into ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/destructive_command_guard.py"
HOOK_ENTRY = {"type": "command", "command": HOOK_COMMAND}


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8") or "{}")
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    for item in pre_tool_use:
        if item.get("matcher") == "Bash":
            command_hooks = item.setdefault("hooks", [])
            if HOOK_ENTRY not in command_hooks:
                command_hooks.append(HOOK_ENTRY)
            break
    else:
        pre_tool_use.append({"matcher": "Bash", "hooks": [HOOK_ENTRY]})

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed destructive command guard in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
