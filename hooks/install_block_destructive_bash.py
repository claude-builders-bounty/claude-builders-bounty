#!/usr/bin/env python3
"""Install the destructive Bash command hook into ~/.claude."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path
from typing import Any


HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
HOOK_SOURCE = Path(__file__).with_name("block_destructive_bash.py")
HOOK_DESTINATION = HOOKS_DIR / "block_destructive_bash.py"
HOOK_COMMAND = f"python3 {HOOK_DESTINATION}"


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}

    with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
        data = json.load(settings_file)

    return data if isinstance(data, dict) else {}


def save_settings(settings: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def install_hook_file() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HOOK_SOURCE, HOOK_DESTINATION)
    HOOK_DESTINATION.chmod(HOOK_DESTINATION.stat().st_mode | stat.S_IXUSR)


def has_hook(hooks: list[Any]) -> bool:
    for group in hooks:
        if not isinstance(group, dict):
            continue
        for hook in group.get("hooks", []):
            if isinstance(hook, dict) and hook.get("command") == HOOK_COMMAND:
                return True
    return False


def install_settings() -> None:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    if not has_hook(pre_tool_use):
        pre_tool_use.append(
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": HOOK_COMMAND}],
            }
        )

    save_settings(settings)


def main() -> int:
    install_hook_file()
    install_settings()
    print(f"Installed hook: {HOOK_DESTINATION}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
