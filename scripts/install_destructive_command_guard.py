#!/usr/bin/env python3
"""Install the destructive command guard into ~/.claude/hooks."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = ROOT / "hooks" / "destructive_command_guard.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOKS_DIR / "destructive_command_guard.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    TARGET_HOOK.chmod(0o755)

    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f'"{sys.executable}" "{TARGET_HOOK}"'
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
                "args": [],
            }
        ],
    }

    def same_hook(existing: dict) -> bool:
        return existing.get("matcher") == "Bash" and any(
            isinstance(hook, dict) and "destructive_command_guard.py" in str(hook.get("command", ""))
            for hook in existing.get("hooks", [])
        )

    if not any(isinstance(item, dict) and same_hook(item) for item in pre_tool_use):
        pre_tool_use.append(entry)

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook: {TARGET_HOOK}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
