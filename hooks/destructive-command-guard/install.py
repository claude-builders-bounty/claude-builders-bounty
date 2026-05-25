#!/usr/bin/env python3
"""Install the destructive command guard hook into the user's Claude config."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


HOOK_DIR = Path.home() / ".claude" / "hooks"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
SOURCE_SCRIPT = Path(__file__).with_name("destructive_command_guard.py")
TARGET_SCRIPT = HOOK_DIR / "destructive-command-guard.py"


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse {SETTINGS_PATH}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{SETTINGS_PATH} must contain a JSON object.")
    return data


def install_script() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_SCRIPT, TARGET_SCRIPT)
    TARGET_SCRIPT.chmod(0o755)


def install_settings() -> None:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    if not isinstance(pre_tool_use, list):
        raise SystemExit("settings.hooks.PreToolUse must be a list.")

    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": str(TARGET_SCRIPT),
            }
        ],
    }

    command_paths = {
        hook.get("command")
        for group in pre_tool_use
        if isinstance(group, dict)
        for hook in group.get("hooks", [])
        if isinstance(hook, dict)
    }
    if str(TARGET_SCRIPT) not in command_paths:
        pre_tool_use.append(entry)

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    install_script()
    install_settings()
    print(f"Installed hook: {TARGET_SCRIPT}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
