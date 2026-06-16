#!/usr/bin/env python3
"""Install the destructive-command hook into ~/.claude."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / ".claude" / "hooks" / "block_destructive_commands.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOKS_DIR / "block_destructive_commands.py"
SETTINGS = CLAUDE_DIR / "settings.json"


def load_settings() -> dict:
    if not SETTINGS.exists():
        return {}
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)

    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": f'"{sys.executable}" "{TARGET_HOOK}"',
            }
        ],
    }

    if entry not in pre_tool_use:
        pre_tool_use.append(entry)

    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook to {TARGET_HOOK}")
    print(f"Updated settings at {SETTINGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
