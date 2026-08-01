#!/usr/bin/env python3
"""Install the guard and merge its PreToolUse entry into user settings."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "block-destructive.py"
TARGET_DIR = Path.home() / ".claude" / "hooks"
TARGET = TARGET_DIR / "block-destructive.py"
SETTINGS = Path.home() / ".claude" / "settings.json"


def quote(path: Path) -> str:
    value = str(path)
    return f'"{value}"' if os.name == "nt" else shlex.quote(value)


def main() -> int:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)

    settings: dict = {}
    if SETTINGS.exists():
        try:
            settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Refusing to overwrite invalid JSON in {SETTINGS}: {exc}")
        if not isinstance(settings, dict):
            raise SystemExit(f"Refusing to overwrite non-object settings in {SETTINGS}")

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f"{quote(Path(sys.executable).resolve())} {quote(TARGET)}"
    handler = {"type": "command", "command": command}

    group = next((item for item in pre_tool_use if item.get("matcher") == "Bash"), None)
    if group is None:
        pre_tool_use.append({"matcher": "Bash", "hooks": [handler]})
    else:
        handlers = group.setdefault("hooks", [])
        if not any(item.get("type") == "command" and item.get("command") == command for item in handlers):
            handlers.append(handler)

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Installed {TARGET}")
    print(f"Updated {SETTINGS}")
    print(f"Blocked attempts will be logged to {TARGET_DIR / 'blocked.log'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
