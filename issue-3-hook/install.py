#!/usr/bin/env python3
"""Quick installer for the block-destructive hook. Usage: python3 install.py"""

import os, json, shutil

HOOK_DIR = os.path.expanduser("~/.claude/hooks")
HOOK_FILE = os.path.join(HOOK_DIR, "block-destructive.py")
SETTINGS_FILE = os.path.join(HOOK_DIR, "settings.json")
SOURCE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block-destructive.py")


def main():
    os.makedirs(HOOK_DIR, exist_ok=True)
    shutil.copy2(SOURCE_FILE, HOOK_FILE)
    os.chmod(HOOK_FILE, 0o755)
    print(f"Installed hook to {HOOK_FILE}")

    hook_entry = {
        "matcher": "Bash",
        "command": f"python3 {HOOK_FILE}"
    }

    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}

    if "hooks" not in settings:
        settings["hooks"] = {}
    if "pre-tool-use" not in settings["hooks"]:
        settings["hooks"]["pre-tool-use"] = []

    existing = settings["hooks"]["pre-tool-use"]
    already_installed = any(
        e.get("command", "").endswith("block-destructive.py") for e in existing
    )

    if not already_installed:
        existing.append(hook_entry)

    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
    print(f"Updated {SETTINGS_FILE}")
    print("\nDone! The hook will now block destructive commands.")


if __name__ == "__main__":
    main()
