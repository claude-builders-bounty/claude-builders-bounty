#!/usr/bin/env python3
"""Install the destructive Bash hook into ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/block_destructive_bash.py"
HOOK_ENTRY: dict[str, Any] = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": HOOK_COMMAND,
        }
    ],
}


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def already_installed(entries: list[Any]) -> bool:
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("matcher") != "Bash":
            continue
        for hook in entry.get("hooks", []):
            if isinstance(hook, dict) and hook.get("command") == HOOK_COMMAND:
                return True
    return False


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    if not isinstance(pre_tool_use, list):
        raise SystemExit("settings.json hooks.PreToolUse must be a list")

    if not already_installed(pre_tool_use):
        pre_tool_use.append(HOOK_ENTRY)

    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed destructive Bash safety hook in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
