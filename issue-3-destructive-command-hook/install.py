#!/usr/bin/env python3
"""Install the destructive command guard into ~/.claude/hooks."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any


SCRIPT_NAME = "block_destructive_commands.py"


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as settings_file:
        data = json.load(settings_file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def hook_already_installed(groups: list[Any], destination: Path) -> bool:
    destination_text = str(destination)
    for group in groups:
        if not isinstance(group, dict):
            continue
        for hook in group.get("hooks", []):
            if not isinstance(hook, dict):
                continue
            command = str(hook.get("command", ""))
            args = [str(arg) for arg in hook.get("args", [])]
            if destination_text == command or destination_text in args:
                return True
    return False


def install_hook(settings: dict[str, Any], destination: Path) -> bool:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must be a JSON object")

    groups = hooks.setdefault("PreToolUse", [])
    if not isinstance(groups, list):
        raise ValueError("settings.hooks.PreToolUse must be a JSON array")

    if hook_already_installed(groups, destination):
        return False

    groups.append(
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": sys.executable,
                    "args": [str(destination)],
                }
            ],
        }
    )
    return True


def main() -> int:
    source = Path(__file__).with_name(SCRIPT_NAME)
    if not source.exists():
        raise FileNotFoundError(f"Missing hook script: {source}")

    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    destination = hooks_dir / SCRIPT_NAME
    shutil.copy2(source, destination)
    current_mode = destination.stat().st_mode
    destination.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = Path.home() / ".claude" / "settings.json"
    settings = load_settings(settings_path)
    changed = install_hook(settings, destination)

    if changed:
        temporary_path = settings_path.with_suffix(".json.tmp")
        with temporary_path.open("w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file, indent=2)
            settings_file.write("\n")
        os.replace(temporary_path, settings_path)

    print(f"Installed hook script: {destination}")
    print(f"Updated settings: {settings_path}" if changed else "Settings already contained this hook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
