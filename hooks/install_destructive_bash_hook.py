#!/usr/bin/env python3
"""Install the destructive Bash command blocker as a Claude Code hook."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import stat
import sys


CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
SOURCE_HOOK = Path(__file__).resolve().with_name("block_destructive_bash.py")
DEST_HOOK = HOOKS_DIR / SOURCE_HOOK.name


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{SETTINGS_PATH} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{SETTINGS_PATH} must contain a JSON object")
    return value


def hook_command() -> str:
    return f'"{sys.executable}" "{DEST_HOOK}"'


def install_hook_file() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, DEST_HOOK)
    try:
        mode = DEST_HOOK.stat().st_mode
        DEST_HOOK.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass


def command_points_to_this_hook(command: str) -> bool:
    return SOURCE_HOOK.name in command


def remove_existing(entries: list) -> list:
    cleaned = []
    for entry in entries:
        if not isinstance(entry, dict):
            cleaned.append(entry)
            continue
        hooks = entry.get("hooks")
        if not isinstance(hooks, list):
            cleaned.append(entry)
            continue
        kept_hooks = [
            hook
            for hook in hooks
            if not (
                isinstance(hook, dict)
                and isinstance(hook.get("command"), str)
                and command_points_to_this_hook(hook["command"])
            )
        ]
        if kept_hooks:
            next_entry = dict(entry)
            next_entry["hooks"] = kept_hooks
            cleaned.append(next_entry)
    return cleaned


def update_settings(settings: dict) -> dict:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit('"hooks" in settings.json must be a JSON object')

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit('"hooks.PreToolUse" in settings.json must be a JSON array')

    pre_tool_use[:] = remove_existing(pre_tool_use)
    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": hook_command(),
                }
            ],
        }
    )
    return settings


def write_settings(settings: dict) -> None:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def main() -> int:
    install_hook_file()
    settings = update_settings(load_settings())
    write_settings(settings)
    print(f"Installed hook: {DEST_HOOK}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
