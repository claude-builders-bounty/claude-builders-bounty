#!/usr/bin/env python3
"""Install the destructive-command guard into ~/.claude/hooks."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "pre_tool_use_block_destructive.py"
HOOK_DIR = Path.home() / ".claude" / "hooks"
SETTINGS = Path.home() / ".claude" / "settings.json"
TARGET = HOOK_DIR / "block-destructive.py"


def main() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    TARGET.chmod(0o755)

    if SETTINGS.exists():
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    else:
        settings = {}

    settings.setdefault("hooks", {})
    settings["hooks"].setdefault("PreToolUse", [])

    hook_group = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": str(TARGET),
            }
        ],
    }

    groups = settings["hooks"]["PreToolUse"]
    if hook_group not in groups:
        groups.append(hook_group)

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook at {TARGET}")
    print(f"Updated settings at {SETTINGS}")


if __name__ == "__main__":
    main()
