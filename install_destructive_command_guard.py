#!/usr/bin/env python3
"""Install the destructive command guard Claude Code hook.

Copies .claude/hooks/destructive_command_guard.py to ~/.claude/hooks/ and adds a
Bash PreToolUse hook entry to ~/.claude/settings.json.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = REPO_ROOT / ".claude" / "hooks" / "destructive_command_guard.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOKS_DIR / "destructive_command_guard.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/destructive_command_guard.py"
HOOK_ENTRY = {"type": "command", "command": HOOK_COMMAND}
PRE_TOOL_USE_ENTRY = {"matcher": "Bash", "hooks": [HOOK_ENTRY]}


def _load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot update invalid JSON in {SETTINGS_PATH}: {exc}") from exc
    if not isinstance(settings, dict):
        raise SystemExit(f"Cannot update {SETTINGS_PATH}: top-level JSON value must be an object")
    return settings


def _ensure_hook_config(settings: dict[str, Any]) -> bool:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"Cannot update {SETTINGS_PATH}: 'hooks' must be an object")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit(f"Cannot update {SETTINGS_PATH}: hooks.PreToolUse must be a list")

    for entry in pre_tool_use:
        if not isinstance(entry, dict) or entry.get("matcher") != "Bash":
            continue
        entry_hooks = entry.setdefault("hooks", [])
        if not isinstance(entry_hooks, list):
            raise SystemExit(f"Cannot update {SETTINGS_PATH}: Bash hooks must be a list")
        if any(isinstance(h, dict) and h.get("command") == HOOK_COMMAND for h in entry_hooks):
            return False
        entry_hooks.append(HOOK_ENTRY)
        return True

    pre_tool_use.append(PRE_TOOL_USE_ENTRY)
    return True


def main() -> int:
    if not SOURCE_HOOK.exists():
        raise SystemExit(f"Hook source not found: {SOURCE_HOOK}")

    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    TARGET_HOOK.chmod(0o755)

    settings = _load_settings()
    changed = _ensure_hook_config(settings)
    if changed or not SETTINGS_PATH.exists():
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    print(f"Installed hook: {TARGET_HOOK}")
    print(f"Updated settings: {SETTINGS_PATH}")
    print("Restart Claude Code for hook changes to take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
