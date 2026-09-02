#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "block_destructive.py"
HOOK_DIR = Path.home() / ".claude" / "hooks"
DEST = HOOK_DIR / "block_destructive.py"
SETTINGS = Path.home() / ".claude" / "settings.json"
ENTRY = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": f"python3 {DEST}"}],
}


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, DEST)
    DEST.chmod(0o755)

    if SETTINGS.exists():
        try:
            data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Refusing to overwrite invalid JSON in {SETTINGS}: {exc}")
    else:
        data = {}

    if not isinstance(data, dict):
        raise SystemExit(f"Refusing to overwrite non-object JSON in {SETTINGS}")

    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    if ENTRY not in pre:
        pre.append(ENTRY)

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook: {DEST}")
    print(f"Updated settings: {SETTINGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
