#!/usr/bin/env python3
"""Install the destructive-command guard into Claude Code user hooks."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS = CLAUDE_DIR / "settings.json"
DEST = HOOKS_DIR / "destructive_command_guard.py"

HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": f"python3 {DEST}",
            "timeout": 5,
            "statusMessage": "Checking command safety",
        }
    ],
}


def main() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "destructive_command_guard.py", DEST)
    DEST.chmod(0o755)

    data = {}
    if SETTINGS.exists():
        data = json.loads(SETTINGS.read_text(encoding="utf-8") or "{}")

    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])

    def is_ours(item: object) -> bool:
        if not isinstance(item, dict) or item.get("matcher") != "Bash":
            return False
        return any(
            isinstance(h, dict)
            and "destructive_command_guard.py" in str(h.get("command", ""))
            for h in item.get("hooks", [])
        )

    pre[:] = [item for item in pre if not is_ours(item)]
    pre.append(HOOK_ENTRY)

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook: {DEST}")
    print(f"Updated settings: {SETTINGS}")


if __name__ == "__main__":
    main()
