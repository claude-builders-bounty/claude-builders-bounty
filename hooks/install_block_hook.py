#!/usr/bin/env python3
"""Install the destructive Bash guard into ~/.claude/hooks and settings.json."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = root / "hooks" / "block_destructive_bash.py"
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    target = hooks_dir / "block_destructive_bash.py"
    shutil.copy2(source, target)

    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        settings = {}

    settings.setdefault("hooks", {})
    pre_tool = settings["hooks"].setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": f"python {target}",
                "args": [],
            }
        ],
    }

    if entry not in pre_tool:
        pre_tool.append(entry)

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook at {target}")
    print(f"Updated settings at {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
