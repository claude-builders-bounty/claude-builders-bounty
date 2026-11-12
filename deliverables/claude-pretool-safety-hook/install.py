#!/usr/bin/env python3
"""Install the hook and register it in Claude Code settings."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
HOOK_DIR = HOME / ".claude" / "hooks"
HOOK_PATH = HOOK_DIR / "block_destructive.py"
SETTINGS_PATH = HOME / ".claude" / "settings.json"

def main():
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "block_destructive.py", HOOK_PATH)
    HOOK_PATH.chmod(0o755)
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Refusing to overwrite invalid settings JSON: {exc}", file=sys.stderr)
            return 1
    else:
        settings = {}
    entries = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    command = f"python3 {HOOK_PATH}"
    duplicate = any(item.get("matcher") == "Bash" and
                    any(h.get("command") == command for h in item.get("hooks", []))
                    for item in entries)
    if not duplicate:
        entries.append({"matcher": "Bash", "hooks": [
            {"type": "command", "command": command, "timeout": 10}
        ]})
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = SETTINGS_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    temporary.replace(SETTINGS_PATH)
    print(f"Installed hook: {HOOK_PATH}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
