#!/usr/bin/env python3
"""Install the destructive Bash command blocker into Claude Code settings."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


HOOK_NAME = "block_destructive_bash.py"


def python_command(hook_path: Path) -> str:
    executable = sys.executable or "python3"
    if os.name == "nt":
        return subprocess.list2cmdline([executable, str(hook_path)])
    return " ".join(shlex.quote(part) for part in (executable, str(hook_path)))


def load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}

    with settings_path.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def save_settings(settings_path: Path, settings: dict) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with settings_path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def add_hook(settings: dict, command: str) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    hook_entry = {"type": "command", "command": command}
    matcher_entry = {"matcher": "Bash", "hooks": [hook_entry]}

    for entry in pre_tool_use:
        if entry.get("matcher") != "Bash":
            continue

        existing_hooks = entry.setdefault("hooks", [])
        for existing_hook in existing_hooks:
            if existing_hook.get("type") == "command" and HOOK_NAME in existing_hook.get("command", ""):
                existing_hook["command"] = command
                return False
        existing_hooks.append(hook_entry)
        return True

    pre_tool_use.append(matcher_entry)
    return True


def main() -> int:
    source_hook = Path(__file__).with_name(HOOK_NAME)
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    installed_hook = hooks_dir / HOOK_NAME
    settings_path = claude_dir / "settings.json"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_hook, installed_hook)

    settings = load_settings(settings_path)
    command = python_command(installed_hook)
    added = add_hook(settings, command)
    save_settings(settings_path, settings)

    action = "Added" if added else "Updated"
    print(f"{action} PreToolUse Bash hook: {command}")
    print(f"Blocked attempts will be logged to: {hooks_dir / 'blocked.log'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
