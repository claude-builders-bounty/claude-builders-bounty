#!/usr/bin/env python3
"""Uninstall the destructive bash guard hook."""

import json
from pathlib import Path

HOOK_DEST = Path.home() / ".claude" / "hooks" / "block-destructive-bash.py"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_NAME = "block-destructive-bash.py"


def main() -> int:
    # 1. Remove the hook file
    if HOOK_DEST.exists():
        HOOK_DEST.unlink()
        print(f"✓ Hook removed: {HOOK_DEST}")
    else:
        print(f"→ Hook not found at {HOOK_DEST}")

    # 2. Remove from settings.json
    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text())
        hooks = settings.get("hooks", [])
        new_hooks = [
            h for h in hooks
            if not (isinstance(h, dict) and h.get("matcher", {}).get("command") == HOOK_NAME)
        ]
        if len(new_hooks) != len(hooks):
            settings["hooks"] = new_hooks
            SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n")
            print(f"✓ Hook unregistered from {SETTINGS_PATH}")
        else:
            print(f"→ Hook not found in settings.json")

    print()
    print("✅ Uninstall complete!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
