"""One-command installer for destructive-bash-guard hook. Idempotent."""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "hooks"
SOURCE_HOOK = Path(__file__).parent / "block_destructive.py"
SETTINGS_FILE = Path.home() / ".claude" / "settings.json"


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    dest_hook = HOOKS_DIR / "block_destructive.py"
    shutil.copy2(SOURCE_HOOK, dest_hook)
    dest_hook.chmod(0o755)
    print(f"OK Hook installed at {dest_hook}")

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    settings: dict = {}
    if SETTINGS_FILE.exists():
        try:
            settings = json.loads(SETTINGS_FILE.read_text())
        except json.JSONDecodeError:
            shutil.copy2(SETTINGS_FILE, SETTINGS_FILE.with_suffix(".json.bak"))
            settings = {}

    hook_entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": f"python3 {dest_hook}"}],
    }
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    already = any(
        any(h.get("command") == hook_entry["hooks"][0]["command"] for h in e.get("hooks", []))
        for e in pre_tool_use
    )
    if already:
        print("OK Hook already registered")
    else:
        pre_tool_use.append(hook_entry)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
        print(f"OK Registered in {SETTINGS_FILE}")

    print(f"\n-> Restart Claude Code to activate\n-> Logs: {HOOKS_DIR / 'blocked.log'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
