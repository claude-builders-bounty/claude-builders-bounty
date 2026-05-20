#!/usr/bin/env python3
"""Install the destructive command PreToolUse hook into Claude Code settings."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path
from typing import Any


SOURCE = Path(__file__).resolve().parent / "block_destructive.py"
HOOK_DIR = Path.home() / ".claude" / "hooks"
TARGET = HOOK_DIR / "block_destructive.py"
SETTINGS = Path.home() / ".claude" / "settings.json"
HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive.py",
        }
    ],
}


def load_settings() -> dict[str, Any]:
    if not SETTINGS.exists():
        return {}
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse {SETTINGS}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{SETTINGS} must contain a JSON object")
    return data


def install_hook_file() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    TARGET.chmod(TARGET.stat().st_mode | stat.S_IXUSR)


def settings_have_entry(entries: list[Any]) -> bool:
    return any(entry == HOOK_ENTRY for entry in entries)


def install_settings_entry() -> None:
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"{SETTINGS} field 'hooks' must be a JSON object")
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit(f"{SETTINGS} field 'hooks.PreToolUse' must be a JSON array")
    if not settings_have_entry(pre_tool_use):
        pre_tool_use.append(HOOK_ENTRY)
    SETTINGS.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    install_hook_file()
    install_settings_entry()
    print(f"Installed destructive command hook at {TARGET}")
    print(f"Updated Claude Code settings at {SETTINGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
