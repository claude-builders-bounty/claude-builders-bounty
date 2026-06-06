#!/usr/bin/env python3
"""Install destructive-command-guard into the current user's Claude settings."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path


HOOK_NAME = "destructive_command_guard.py"


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def install() -> None:
    source = Path(__file__).with_name(HOOK_NAME)
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    target = hooks_dir / HOOK_NAME
    settings_path = claude_dir / "settings.json"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR)

    settings = load_settings(settings_path)
    pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    command = {
        "type": "command",
        "command": sys.executable,
        "args": [str(target)],
    }
    group = {"matcher": "Bash", "hooks": [command]}

    already_installed = any(
        item.get("matcher") == "Bash"
        and any(hook.get("args") == [str(target)] for hook in item.get("hooks", []))
        for item in pre_tool_use
        if isinstance(item, dict)
    )
    if not already_installed:
        pre_tool_use.append(group)

    save_settings(settings_path, settings)
    print(f"Installed {target}")
    print(f"Updated {settings_path}")


if __name__ == "__main__":
    install()
