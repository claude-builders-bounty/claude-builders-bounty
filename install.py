#!/usr/bin/env python3
"""Install the destructive Bash guard into Claude Code's user hooks."""

from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = REPO_ROOT / "hooks" / "block_destructive_bash.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOKS_DIR / "block_destructive_bash.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"

HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive_bash.py",
        }
    ],
}


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}

    with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def hook_entry_exists(entries: list[Any]) -> bool:
    expected_command = HOOK_ENTRY["hooks"][0]["command"]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for hook in entry.get("hooks", []):
            if isinstance(hook, dict) and hook.get("command") == expected_command:
                return True
    return False


def install_hook_file() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    mode = TARGET_HOOK.stat().st_mode
    TARGET_HOOK.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def update_settings() -> bool:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    if hook_entry_exists(pre_tool_use):
        return False

    pre_tool_use.append(HOOK_ENTRY)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write(os.linesep)

    return True


def main() -> int:
    install_hook_file()
    settings_changed = update_settings()
    print(f"Installed hook: {TARGET_HOOK}")
    if settings_changed:
        print(f"Registered PreToolUse Bash hook in: {SETTINGS_PATH}")
    else:
        print(f"PreToolUse Bash hook was already registered in: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
