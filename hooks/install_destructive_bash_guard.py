#!/usr/bin/env python3
"""Install the destructive Bash guard into Claude Code user settings."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = REPO_ROOT / "hooks" / "destructive_bash_guard.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOK_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOK_DIR / "destructive_bash_guard.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
HOOK_COMMAND = f"python3 {TARGET_HOOK}"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_settings(settings: dict) -> None:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def hook_entry_exists(entries: list[dict]) -> bool:
    for entry in entries:
        if entry.get("matcher") != "Bash":
            continue
        for hook in entry.get("hooks", []):
            if hook.get("type") == "command" and hook.get("command") == HOOK_COMMAND:
                return True
    return False


def install() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    TARGET_HOOK.chmod(0o755)

    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not hook_entry_exists(pre_tool_use):
        pre_tool_use.append(
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": HOOK_COMMAND,
                    }
                ],
            }
        )
    save_settings(settings)


if __name__ == "__main__":
    install()
    print(f"Installed {TARGET_HOOK}")
    print(f"Updated {SETTINGS_PATH}")
