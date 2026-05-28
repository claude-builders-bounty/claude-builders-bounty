#!/usr/bin/env python3
"""Install the destructive Bash command blocker hook for Claude Code."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOME = Path.home()
HOOK_DIR = HOME / ".claude" / "hooks"
SETTINGS_PATH = HOME / ".claude" / "settings.json"
HOOK_SOURCE = ROOT / "block_destructive_bash.py"
HOOK_TARGET = HOOK_DIR / "block_destructive_bash.py"
HOOK_COMMAND = "python3 ~/.claude/hooks/block_destructive_bash.py"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = SETTINGS_PATH.with_suffix(".json.bak")
        shutil.copy2(SETTINGS_PATH, backup)
        return {}


def install_hook_file() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HOOK_SOURCE, HOOK_TARGET)
    HOOK_TARGET.chmod(0o755)


def update_settings() -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    }

    for existing in pre_tool_use:
        if existing.get("matcher") != "Bash":
            continue
        hook_list = existing.setdefault("hooks", [])
        if not any(hook.get("command") == HOOK_COMMAND for hook in hook_list):
            hook_list.append(entry["hooks"][0])
        break
    else:
        pre_tool_use.append(entry)

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    install_hook_file()
    update_settings()
    print(f"Installed destructive command blocker to {HOOK_TARGET}")
    print(f"Updated Claude Code settings at {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
