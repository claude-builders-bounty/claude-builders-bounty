#!/usr/bin/env python3
"""Install the destructive Bash guard into ~/.claude/settings.json."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = ROOT / ".claude" / "hooks" / "block_destructive_bash.py"


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def main() -> int:
    home = Path.home()
    hook_dir = home / ".claude" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)

    target_hook = hook_dir / SOURCE_HOOK.name
    shutil.copy2(SOURCE_HOOK, target_hook)

    settings_path = home / ".claude" / "settings.json"
    settings = load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    handler = {
        "type": "command",
        "command": sys.executable,
        "args": [str(target_hook)],
    }
    entry = {
        "matcher": "Bash",
        "hooks": [handler],
    }

    already_present = False
    for existing in pre_tool_use:
        if existing.get("matcher") != "Bash":
            continue
        existing_hooks = existing.setdefault("hooks", [])
        if handler in existing_hooks:
            already_present = True
            break
        existing_hooks.append(handler)
        already_present = True
        break

    if not already_present:
        pre_tool_use.append(entry)

    save_settings(settings_path, settings)
    print(f"Installed hook: {target_hook}")
    print(f"Updated settings: {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
