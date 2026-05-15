#!/usr/bin/env python3
"""Install the destructive command guard into Claude Code settings."""

from __future__ import annotations

import json
from pathlib import Path


HOME = Path.home()
HOOK_PATH = str(HOME / ".claude" / "hooks" / "pre_tool_use.py")
SETTINGS_PATH = HOME / ".claude" / "settings.json"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def main() -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    matcher_config = {"matcher": "Bash", "hooks": [{"type": "command", "command": HOOK_PATH}]}

    existing_commands = {
        hook.get("command")
        for entry in pre_tool_use
        for hook in entry.get("hooks", [])
        if isinstance(hook, dict)
    }
    if HOOK_PATH not in existing_commands:
        pre_tool_use.append(matcher_config)

    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed destructive command guard in {SETTINGS_PATH}")


if __name__ == "__main__":
    main()
