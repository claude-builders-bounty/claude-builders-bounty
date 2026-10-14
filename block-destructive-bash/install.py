#!/usr/bin/env python3
"""install.py -- merge the block-destructive hook into ~/.claude/settings.json.

Idempotent: running it twice changes nothing. Creates settings.json if it
does not exist; backs an existing file up to settings.json.bak first; refuses
to touch a settings file it cannot parse. Writes the hook command with the
real absolute home path so no shell expansion is needed at hook runtime.
"""

import json
import shutil
import sys
from pathlib import Path

HOME = Path.home()
SETTINGS = HOME / ".claude" / "settings.json"
HOOK_CMD = 'python3 "%s"' % (HOME / ".claude" / "hooks" / "block_destructive.py")


def main():
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if SETTINGS.exists():
        shutil.copy2(SETTINGS, SETTINGS.with_suffix(".json.bak"))
        try:
            data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            sys.exit(
                "ERROR: %s is not valid JSON (%s); refusing to overwrite it. "
                "Fix it by hand, then re-run install.sh." % (SETTINGS, exc)
            )

    pre_tool_use = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    for group in pre_tool_use:
        for handler in group.get("hooks", []):
            if handler.get("command") == HOOK_CMD:
                print("Already installed: %s" % HOOK_CMD)
                return

    pre_tool_use.append({
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_CMD}],
    })
    SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("Installed hook into %s" % SETTINGS)
    print("  matcher: Bash   command: %s" % HOOK_CMD)


if __name__ == "__main__":
    main()
