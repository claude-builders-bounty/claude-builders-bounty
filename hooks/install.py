#!/usr/bin/env python3
"""Install the destructive Bash command guard for Claude Code."""

from __future__ import annotations

import json
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = REPO_ROOT / "hooks" / "pre_tool_use_guard.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOKS_DIR / "pre_tool_use_guard.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
HOOK_COMMAND = f"{shlex.quote(sys.executable)} {shlex.quote(str(TARGET_HOOK))}"


def main() -> int:
    install_hook_file()
    settings = load_settings()
    changed = ensure_hook_registered(settings)
    write_settings(settings)

    status = "registered" if changed else "already registered"
    print(f"Installed {TARGET_HOOK}")
    print(f"PreToolUse Bash hook {status} in {SETTINGS_PATH}")
    return 0


def install_hook_file() -> None:
    try:
        HOOKS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
        TARGET_HOOK.chmod(0o755)
    except OSError as exc:
        raise SystemExit(
            f"Cannot install hook from {SOURCE_HOOK} to {TARGET_HOOK}: {exc}"
        ) from exc


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}

    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse {SETTINGS_PATH}: {exc}") from exc

    if not isinstance(settings, dict):
        raise SystemExit(f"{SETTINGS_PATH} must contain a JSON object")

    return settings


def ensure_hook_registered(settings: dict[str, Any]) -> bool:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit("settings.hooks must be a JSON object")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit("settings.hooks.PreToolUse must be a JSON array")

    bash_entry = find_bash_entry(pre_tool_use)
    if bash_entry is None:
        bash_entry = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_entry)

    entry_hooks = bash_entry.setdefault("hooks", [])
    if not isinstance(entry_hooks, list):
        raise SystemExit("Bash PreToolUse hooks must be a JSON array")

    hook = {"type": "command", "command": HOOK_COMMAND}
    if hook in entry_hooks:
        return False

    entry_hooks.append(hook)
    return True


def find_bash_entry(pre_tool_use: list[Any]) -> dict[str, Any] | None:
    for entry in pre_tool_use:
        if isinstance(entry, dict) and entry.get("matcher") == "Bash":
            return entry
    return None


def write_settings(settings: dict[str, Any]) -> None:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
