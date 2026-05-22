#!/usr/bin/env python3
"""Install the destructive Bash blocker as a Claude Code PreToolUse hook."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = ROOT / "hooks" / "block-destructive-bash.py"
DEST_DIR = Path.home() / ".claude" / "hooks"
DEST_HOOK = DEST_DIR / "block-destructive-bash.py"
SETTINGS = Path.home() / ".claude" / "settings.json"


def _load_settings():
    if not SETTINGS.exists():
        return {}

    try:
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = SETTINGS.with_name(f"{SETTINGS.name}.bak.{int(time.time())}")
        shutil.copy2(SETTINGS, backup)
        return {}

    return settings if isinstance(settings, dict) else {}


def _write_settings(settings) -> None:
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def _register_hook(settings) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = str(DEST_HOOK)

    for matcher in pre_tool_use:
        if matcher.get("matcher") != "Bash":
            continue
        for hook in matcher.get("hooks", []):
            if hook.get("type") == "command" and hook.get("command") == command:
                return False

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                }
            ],
        }
    )
    return True


def main() -> int:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, DEST_HOOK)
    os.chmod(DEST_HOOK, 0o755)

    settings = _load_settings()
    changed = _register_hook(settings)
    _write_settings(settings)

    status = "registered" if changed else "already registered"
    print(f"Installed {DEST_HOOK}")
    print(f"Hook {status} in {SETTINGS}")
    print("Run /hooks inside Claude Code to verify the PreToolUse Bash matcher.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
