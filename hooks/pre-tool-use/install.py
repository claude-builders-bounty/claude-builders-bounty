#!/usr/bin/env python3
"""Install script for the destructive bash blocker hook."""

import json
import os
import shutil
import sys

HOOK_DIR = os.path.expanduser("~/.claude/hooks")
SETTINGS_FILE = os.path.expanduser("~/.claude/settings.json")
HOOK_SCRIPT = "block-destructive-bash.py"


def install():
    """Install the hook to ~/.claude/hooks/ and update settings.json."""
    # 1. Copy hook script
    os.makedirs(HOOK_DIR, exist_ok=True)
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), HOOK_SCRIPT)
    dst = os.path.join(HOOK_DIR, HOOK_SCRIPT)
    shutil.copy2(src, dst)
    os.chmod(dst, 0o755)
    print(f"✅ Copied {HOOK_SCRIPT} → {dst}")

    # 2. Update settings.json
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)

    # Add hook entry
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("pre-tool-use", [])

    hook_entry = {
        "matcher": "Bash",
        "hooks": [f"python3 {dst}"],
    }

    # Check if already installed
    for entry in pre_tool_use:
        if HOOK_SCRIPT in str(entry.get("hooks", [])):
            print("ℹ️  Hook already registered in settings.json")
            break
    else:
        pre_tool_use.append(hook_entry)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        print(f"✅ Registered hook in {SETTINGS_FILE}")

    print("\n🎉 Installation complete! Destructive bash commands are now blocked.")


if __name__ == "__main__":
    install()
