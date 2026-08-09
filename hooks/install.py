#!/usr/bin/env python3
"""Install the destructive Bash guard and merge its global hook setting."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "block-destructive-bash.py"
CLAUDE_HOME = Path.home() / ".claude"
TARGET_DIR = CLAUDE_HOME / "hooks"
TARGET = TARGET_DIR / SOURCE.name
SETTINGS = CLAUDE_HOME / "settings.json"


def _load_settings() -> Dict[str, Any]:
    if not SETTINGS.exists():
        return {}
    try:
        value = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Cannot safely update {SETTINGS}: {error}")
    if not isinstance(value, dict):
        raise SystemExit(f"Cannot safely update {SETTINGS}: the root value is not an object")
    return value


def _merge_hook(settings: Dict[str, Any]) -> None:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"Cannot safely update {SETTINGS}: hooks is not an object")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit(f"Cannot safely update {SETTINGS}: PreToolUse is not an array")

    command = f'"{sys.executable}" "{TARGET}"'
    handler = {"type": "command", "command": command}

    for group in pre_tool_use:
        if not isinstance(group, dict) or group.get("matcher") != "Bash":
            continue
        group_hooks = group.setdefault("hooks", [])
        if not isinstance(group_hooks, list):
            raise SystemExit(f"Cannot safely update {SETTINGS}: a Bash hook group has invalid hooks")
        if not any(isinstance(item, dict) and item.get("command") == command for item in group_hooks):
            group_hooks.append(handler)
        return

    pre_tool_use.append({"matcher": "Bash", "hooks": [handler]})


def main() -> int:
    if not SOURCE.exists():
        raise SystemExit(f"Missing hook source: {SOURCE}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    TARGET.chmod(TARGET.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings = _load_settings()
    _merge_hook(settings)
    CLAUDE_HOME.mkdir(parents=True, exist_ok=True)
    if SETTINGS.exists():
        backup = SETTINGS.with_suffix(SETTINGS.suffix + ".before-destructive-hook")
        if not backup.exists():
            shutil.copy2(SETTINGS, backup)
    SETTINGS.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Installed {TARGET}")
    print(f"Merged PreToolUse/Bash hook into {SETTINGS}")
    print("Restart Claude Code or run /hooks to verify the hook is listed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
