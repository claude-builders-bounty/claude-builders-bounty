#!/usr/bin/env python3
"""Install the destructive command guard into Claude Code settings."""

from __future__ import annotations

import json
import os
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = str(Path.home() / ".claude" / "hooks" / "destructive_command_guard.py")


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        backup = SETTINGS_PATH.with_suffix(".json.bak")
        SETTINGS_PATH.replace(backup)
        print(f"Existing invalid settings moved to {backup}")
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    }

    if entry not in pre_tool_use:
        pre_tool_use.append(entry)

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = SETTINGS_PATH.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")
    os.replace(temp_path, SETTINGS_PATH)
    print(f"Installed PreToolUse hook in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
