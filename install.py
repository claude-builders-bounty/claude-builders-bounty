#!/usr/bin/env python3
"""Install the destructive Bash blocker hook for Claude Code."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / ".claude" / "hooks" / "block-destructive-bash.py"
HOOK_DIR = Path.home() / ".claude" / "hooks"
HOOK_PATH = HOOK_DIR / "block-destructive-bash.py"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": str(HOOK_PATH),
        }
    ],
}


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


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, HOOK_PATH)
    HOOK_PATH.chmod(0o755)

    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    already_installed = any(
        entry.get("matcher") == "Bash"
        and any(hook.get("command") == str(HOOK_PATH) for hook in entry.get("hooks", []))
        for entry in pre_tool_use
        if isinstance(entry, dict)
    )
    if not already_installed:
        pre_tool_use.append(HOOK_ENTRY)
        save_settings(settings)

    print(f"Installed hook: {HOOK_PATH}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
