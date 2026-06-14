#!/usr/bin/env python3
"""Install the destructive Bash guard into ~/.claude/hooks/."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = REPO_ROOT / "hooks" / "block_destructive_bash.py"
CLAUDE_DIR = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")).expanduser()
HOOK_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOK_DIR / "block_destructive_bash.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": f'"{sys.executable}" "{TARGET_HOOK}"'}],
}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
            return json.load(settings_file)
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Cannot read valid Claude settings from {SETTINGS_PATH}: {exc}") from exc


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    TARGET_HOOK.chmod(TARGET_HOOK.stat().st_mode | stat.S_IXUSR)

    try:
        settings = load_settings()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    if HOOK_ENTRY not in pre_tool_use:
        pre_tool_use.append(HOOK_ENTRY)

    temporary_settings = SETTINGS_PATH.with_suffix(".json.tmp")
    with temporary_settings.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")
    temporary_settings.replace(SETTINGS_PATH)

    print(f"Installed hook: {TARGET_HOOK}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
