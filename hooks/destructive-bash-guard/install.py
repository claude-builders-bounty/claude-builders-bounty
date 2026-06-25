#!/usr/bin/env python3
"""Install the destructive Bash guard hook into ~/.claude/hooks."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / "block_destructive_bash.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOKS_DIR / "block_destructive_bash.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_settings(settings: dict[str, Any]) -> None:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def hook_command() -> str:
    python = os.environ.get("PYTHON", sys.executable)
    return f'{python} "{TARGET_HOOK}"'


def ensure_hook_settings(settings: dict[str, Any]) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": hook_command(),
            }
        ],
    }

    if entry in pre_tool_use:
        return False

    pre_tool_use.append(entry)
    return True


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)

    settings = load_settings()
    changed = ensure_hook_settings(settings)
    if changed:
        save_settings(settings)

    print(f"Installed hook: {TARGET_HOOK}")
    print(f"Updated settings: {SETTINGS_PATH}")
    print("Blocked attempts will be logged to ~/.claude/hooks/blocked.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
