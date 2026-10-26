#!/usr/bin/env python3
"""install.py — install the block-destructive hook into ~/.claude/settings.json.

Merges the PreToolUse Bash hook entry without clobbering existing hooks.
"""
import json
import os
import shutil

HOME = os.path.expanduser("~")
CLAUDE_DIR = os.path.join(HOME, ".claude")
SETTINGS = os.path.join(CLAUDE_DIR, "settings.json")
HOOK_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block-destructive.py")
HOOK_DST = os.path.join(CLAUDE_DIR, "hooks", "block-destructive.py")


def main():
    os.makedirs(os.path.join(CLAUDE_DIR, "hooks"), exist_ok=True)
    shutil.copyfile(HOOK_SRC, HOOK_DST)

    settings = {}
    if os.path.exists(SETTINGS):
        with open(SETTINGS, encoding="utf-8") as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}

    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": f"python {HOOK_DST}"}],
    }
    # Avoid duplicate entries.
    for e in pre:
        if e.get("matcher") == "Bash" and any(
            "block-destructive.py" in h.get("command", "") for h in e.get("hooks", [])
        ):
            print("Hook already installed.")
            break
    else:
        pre.append(entry)

    with open(SETTINGS, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    print(f"Installed hook to {HOOK_DST}")
    print(f"Updated {SETTINGS}")


if __name__ == "__main__":
    main()
