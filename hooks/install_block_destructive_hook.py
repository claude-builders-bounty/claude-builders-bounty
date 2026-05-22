#!/usr/bin/env python3
"""Install the destructive Bash guard hook into ~/.claude."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


HOME_CLAUDE = Path.home() / ".claude"
HOOKS_DIR = HOME_CLAUDE / "hooks"
SETTINGS_PATH = HOME_CLAUDE / "settings.json"
SOURCE_HOOK = Path(__file__).with_name("block_destructive_bash.py")
TARGET_HOOK = HOOKS_DIR / "block_destructive_bash.py"


def _load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def _write_settings(settings: dict[str, Any]) -> None:
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def _hook_entry() -> dict[str, Any]:
    return {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": str(TARGET_HOOK),
            }
        ],
    }


def _install_settings() -> None:
    settings = _load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    target_command = str(TARGET_HOOK)
    already_installed = any(
        isinstance(group, dict)
        and any(
            isinstance(hook, dict) and hook.get("command") == target_command
            for hook in group.get("hooks", [])
        )
        for group in pre_tool_use
    )

    if not already_installed:
        pre_tool_use.append(_hook_entry())

    _write_settings(settings)


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    TARGET_HOOK.chmod(0o755)
    _install_settings()
    print(f"Installed destructive Bash guard hook at {TARGET_HOOK}")
    print(f"Updated Claude Code settings at {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
