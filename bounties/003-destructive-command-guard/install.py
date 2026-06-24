#!/usr/bin/env python3
"""Install the destructive command guard into ~/.claude."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
HOOK_PATH = HOOKS_DIR / "pre_tool_use_guard.py"


HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_guard.py",
            "timeout": 5,
        }
    ],
}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def install_hook() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "pre_tool_use_guard.py", HOOK_PATH)
    HOOK_PATH.chmod(0o755)


def merge_settings() -> None:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    already_installed = any(
        item.get("matcher") == "Bash"
        and any(
            "pre_tool_use_guard.py" in hook.get("command", "")
            for hook in item.get("hooks", [])
            if isinstance(hook, dict)
        )
        for item in pre_tool_use
        if isinstance(item, dict)
    )
    if not already_installed:
        pre_tool_use.append(HOOK_ENTRY)

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def main() -> None:
    install_hook()
    merge_settings()
    print(f"Installed hook: {HOOK_PATH}")
    print(f"Updated settings: {SETTINGS_PATH}")


if __name__ == "__main__":
    main()
