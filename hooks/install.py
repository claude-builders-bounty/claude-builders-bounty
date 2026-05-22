#!/usr/bin/env python3
"""Install the destructive Bash command hook into ~/.claude/settings.json."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = ROOT / "hooks" / "block-dangerous-bash.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOK_DIR = CLAUDE_DIR / "hooks"
DEST_HOOK = HOOK_DIR / "block-dangerous-bash.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def install_hook() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, DEST_HOOK)
    DEST_HOOK.chmod(0o755)


def hook_command() -> str:
    return f'"{sys.executable}" "{DEST_HOOK}"'


def update_settings(settings: dict) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    desired = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": hook_command(),
            }
        ],
    }

    for item in pre_tool_use:
        if item == desired:
            return False

    pre_tool_use.append(desired)
    return True


def main() -> int:
    install_hook()
    settings = load_settings()
    changed = update_settings(settings)
    save_settings(settings)

    if changed:
        print(f"Installed hook and updated {SETTINGS_PATH}")
    else:
        print(f"Hook already configured in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
