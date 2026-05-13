#!/usr/bin/env python3
"""Install the destructive-command hook into ~/.claude/hooks."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List


HOOK_COMMAND = "python ~/.claude/hooks/block_destructive_commands.py"


def load_settings(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def ensure_hook(settings: Dict[str, Any]) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use: List[Dict[str, Any]] = hooks.setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    }

    for existing in pre_tool_use:
        if existing == entry:
            return False

    pre_tool_use.append(entry)
    return True


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = root / "hooks" / "block_destructive_commands.py"
    hooks_dir = Path.home() / ".claude" / "hooks"
    settings_path = Path.home() / ".claude" / "settings.json"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, hooks_dir / source.name)

    settings = load_settings(settings_path)
    changed = ensure_hook(settings)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    print(f"Installed {hooks_dir / source.name}")
    print(f"{'Updated' if changed else 'Kept'} {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
