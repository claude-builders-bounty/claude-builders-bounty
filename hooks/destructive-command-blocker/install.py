#!/usr/bin/env python3
"""Install the destructive Bash blocker hook into Claude Code settings."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


HOOK_COMMAND = "python ~/.claude/hooks/block_destructive_bash.py"
HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": HOOK_COMMAND,
        }
    ],
}


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def hook_already_present(settings: dict) -> bool:
    for entry in settings.get("hooks", {}).get("PreToolUse", []):
        if not isinstance(entry, dict):
            continue
        for hook in entry.get("hooks", []):
            if isinstance(hook, dict) and hook.get("command") == HOOK_COMMAND:
                return True
    return False


def main() -> int:
    source_dir = Path(__file__).resolve().parent
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"
    hook_target = hooks_dir / "block_destructive_bash.py"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_dir / "block_destructive_bash.py", hook_target)
    hook_target.chmod(0o755)

    settings = load_settings(settings_path)
    settings.setdefault("hooks", {})
    settings["hooks"].setdefault("PreToolUse", [])

    if not hook_already_present(settings):
        settings["hooks"]["PreToolUse"].append(HOOK_ENTRY)

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed hook at {hook_target}")
    print(f"Updated settings at {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

