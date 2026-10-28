#!/usr/bin/env python3
"""One-command install: copy the hook and register it in ~/.claude/settings.json."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

HOOK_NAME = "block_destructive.py"
SETTINGS_HOOK = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": str(Path.home() / ".claude" / "hooks" / HOOK_NAME),
        }
    ],
}


def main() -> int:
    src = Path(__file__).resolve().parent / HOOK_NAME
    dest_dir = Path.home() / ".claude" / "hooks"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / HOOK_NAME
    shutil.copy2(src, dest)
    dest.chmod(0o755)

    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8") or "{}")
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    already = any(
        isinstance(item, dict)
        and any(
            (h.get("command") or "").endswith(HOOK_NAME)
            for h in (item.get("hooks") or [])
            if isinstance(h, dict)
        )
        for item in pre
    )
    if not already:
        pre.append(SETTINGS_HOOK)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    print(f"Installed {dest}")
    print(f"Registered PreToolUse Bash matcher in {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
