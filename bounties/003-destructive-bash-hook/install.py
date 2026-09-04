#!/usr/bin/env python3
"""Install the destructive Bash guard into the current user's Claude settings."""

from __future__ import annotations

import json
import shlex
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / "destructive_bash_guard.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOK_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
INSTALLED_HOOK = HOOK_DIR / "destructive_bash_guard.py"
HOOK_COMMAND = f"{shlex.quote(sys.executable)} {shlex.quote(str(INSTALLED_HOOK))}"


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, INSTALLED_HOOK)

    settings = _load_settings()
    hooks_root = settings.setdefault("hooks", {})
    if not isinstance(hooks_root, dict):
        raise SystemExit("~/.claude/settings.json has a non-object 'hooks' value")

    pre_tool_hooks = hooks_root.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_hooks, list):
        raise SystemExit("~/.claude/settings.json has a non-list hooks.PreToolUse value")

    hook_group = _bash_hook_group(pre_tool_hooks)
    hooks = hook_group.setdefault("hooks", [])
    if not isinstance(hooks, list):
        raise SystemExit("Existing Bash PreToolUse group has a non-list 'hooks' value")

    if not any(isinstance(hook, dict) and hook.get("command") == HOOK_COMMAND for hook in hooks):
        hooks.append({"type": "command", "command": HOOK_COMMAND})

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook at {INSTALLED_HOOK}")
    print(f"Updated settings at {SETTINGS_PATH}")
    return 0


def _load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}

    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {SETTINGS_PATH}: {exc}") from exc
    if not isinstance(settings, dict):
        raise SystemExit(f"{SETTINGS_PATH} must contain a JSON object")

    backup = SETTINGS_PATH.with_suffix(".json.bak")
    if not backup.exists():
        shutil.copy2(SETTINGS_PATH, backup)
    return settings


def _bash_hook_group(pre_tool_hooks: list[dict]) -> dict:
    for group in pre_tool_hooks:
        if isinstance(group, dict) and group.get("matcher") == "Bash":
            return group
    group = {"matcher": "Bash", "hooks": []}
    pre_tool_hooks.append(group)
    return group


if __name__ == "__main__":
    raise SystemExit(main())
