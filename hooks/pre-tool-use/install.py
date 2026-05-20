#!/usr/bin/env python3
"""Install the destructive Bash guard into Claude Code user settings."""

from __future__ import annotations

import json
import shlex
import shutil
import stat
from pathlib import Path


REPO_HOOK = Path(__file__).with_name("destructive-bash-guard.py")
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
INSTALLED_HOOK = HOOKS_DIR / "destructive-bash-guard.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def _load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open(encoding="utf-8") as settings_file:
        return json.load(settings_file)


def _write_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def _install_hook_script() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_HOOK, INSTALLED_HOOK)
    mode = INSTALLED_HOOK.stat().st_mode
    INSTALLED_HOOK.chmod(mode | stat.S_IXUSR)


def _hook_entry() -> dict:
    command = shlex.quote(str(INSTALLED_HOOK))
    return {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }


def _merge_settings(settings: dict) -> dict:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = shlex.quote(str(INSTALLED_HOOK))

    for matcher in pre_tool_use:
        if matcher.get("matcher") != "Bash":
            continue
        commands = matcher.setdefault("hooks", [])
        if not any(hook.get("command") == command for hook in commands):
            commands.append({"type": "command", "command": command})
        return settings

    pre_tool_use.append(_hook_entry())
    return settings


def main() -> int:
    _install_hook_script()
    settings = _merge_settings(_load_settings())
    _write_settings(settings)
    print(f"Installed destructive Bash guard at {INSTALLED_HOOK}")
    print(f"Updated Claude Code settings at {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
