#!/usr/bin/env python3
"""Install Destructive Bash Guard into the user's Claude Code hooks."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


SOURCE = Path(__file__).with_name("destructive_bash_guard.py")
HOOK_DIR = Path.home() / ".claude" / "hooks"
TARGET = HOOK_DIR / "destructive_bash_guard.py"
SETTINGS = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = 'python3 "$HOME/.claude/hooks/destructive_bash_guard.py"'


def load_settings() -> dict:
    if not SETTINGS.exists():
        return {}
    with SETTINGS.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def install_hook_file() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    TARGET.chmod(0o755)


def merge_settings(settings: dict) -> dict:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    bash_group = None
    for group in pre_tool_use:
        if group.get("matcher") == "Bash":
            bash_group = group
            break

    if bash_group is None:
        bash_group = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_group)

    command_hooks = bash_group.setdefault("hooks", [])
    if not any(hook.get("type") == "command" and hook.get("command") == HOOK_COMMAND for hook in command_hooks):
        command_hooks.append(
            {
                "type": "command",
                "command": HOOK_COMMAND,
                "timeout": 5,
            }
        )

    return settings


def save_settings(settings: dict) -> None:
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def main() -> int:
    install_hook_file()
    save_settings(merge_settings(load_settings()))
    print(f"Installed hook: {TARGET}")
    print(f"Updated settings: {SETTINGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
