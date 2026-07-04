#!/usr/bin/env python3
"""Install the destructive Bash guard hook into ~/.claude."""

from __future__ import annotations

import json
import pathlib
import shutil
import stat


HOOK_NAME = "block_destructive_bash.py"
SETTINGS_HOOK = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py",
        }
    ],
}


def load_settings(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as settings_file:
        loaded = json.load(settings_file)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def has_hook(pre_tool_use: list) -> bool:
    for item in pre_tool_use:
        if item == SETTINGS_HOOK:
            return True
    return False


def install() -> None:
    source_dir = pathlib.Path(__file__).resolve().parent
    claude_dir = pathlib.Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    target_hook = hooks_dir / HOOK_NAME
    shutil.copy2(source_dir / HOOK_NAME, target_hook)
    target_hook.chmod(target_hook.stat().st_mode | stat.S_IXUSR)

    settings_path = claude_dir / "settings.json"
    settings = load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise ValueError("settings.hooks.PreToolUse must be a list")
    if not has_hook(pre_tool_use):
        pre_tool_use.append(SETTINGS_HOOK)

    with settings_path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed {target_hook}")
    print(f"Updated {settings_path}")


if __name__ == "__main__":
    install()
