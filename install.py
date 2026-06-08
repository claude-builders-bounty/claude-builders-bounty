#!/usr/bin/env python3
"""Install the destructive command guard into the user's Claude Code hooks."""

from __future__ import annotations

import json
import shutil
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / "hooks" / "destructive-command-guard.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOKS_DIR / "destructive-command-guard.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def _load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def _save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def _hook_entry() -> dict:
    command = f'"{sys.executable}" "{TARGET_HOOK}"'
    return {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }


def _entry_exists(entries: list[dict]) -> bool:
    expected_command = f'"{sys.executable}" "{TARGET_HOOK}"'
    for entry in entries:
        if entry.get("matcher") != "Bash":
            continue
        hooks = entry.get("hooks") or []
        if any(hook.get("command") == expected_command for hook in hooks if isinstance(hook, dict)):
            return True
    return False


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    TARGET_HOOK.chmod(TARGET_HOOK.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings = _load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not _entry_exists(pre_tool_use):
        pre_tool_use.append(_hook_entry())
        _save_settings(settings)

    print(f"Installed hook: {TARGET_HOOK}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
