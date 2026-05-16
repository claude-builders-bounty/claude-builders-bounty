#!/usr/bin/env python3
"""Install the destructive Bash guard hook for Claude Code."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

HOOK_NAME = "block-destructive-bash.py"
SOURCE = Path(__file__).with_name(HOOK_NAME)
HOOK_DIR = Path.home() / ".claude" / "hooks"
TARGET = HOOK_DIR / HOOK_NAME
SETTINGS = Path.home() / ".claude" / "settings.json"
ENTRY = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": str(TARGET)}],
}


def load_settings() -> dict:
    if not SETTINGS.exists() or not SETTINGS.read_text(encoding="utf-8").strip():
        return {}
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    TARGET.chmod(0o755)

    data = load_settings()
    pre_tool_use = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if ENTRY not in pre_tool_use:
        pre_tool_use.append(ENTRY)
    SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"Installed {TARGET}")
    print(f"Updated {SETTINGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
