#!/usr/bin/env python3
"""Install the destructive Bash guard into ~/.claude/settings.json.

This script preserves existing settings and appends the hook only if the same
command is not already configured.
"""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/destructive_bash_guard.py"
HOOK_ENTRY = {"type": "command", "command": HOOK_COMMAND}
PRE_TOOL_ENTRY = {"matcher": "Bash", "hooks": [HOOK_ENTRY]}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected {SETTINGS_PATH} to contain a JSON object")
    return data


def main() -> int:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit("hooks.PreToolUse must be a list")

    for entry in pre_tool_use:
        if not isinstance(entry, dict):
            continue
        if entry.get("matcher") != "Bash":
            continue
        existing_hooks = entry.setdefault("hooks", [])
        if any(isinstance(h, dict) and h.get("command") == HOOK_COMMAND for h in existing_hooks):
            print(f"Already installed in {SETTINGS_PATH}")
            return 0
        existing_hooks.append(HOOK_ENTRY)
        break
    else:
        pre_tool_use.append(PRE_TOOL_ENTRY)

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")
    print(f"Installed destructive Bash guard in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
