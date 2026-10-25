#!/usr/bin/env python3
"""Install the hook and merge its registration into user settings."""

import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile


def install():
    config = Path.home() / ".claude"
    settings = config / "settings.json"
    original = settings.read_bytes() if settings.exists() else None
    data = json.loads(original) if original else {}
    if not isinstance(data, dict):
        raise ValueError("settings.json must contain an object")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings hooks must be an object")
    groups = hooks.setdefault("PreToolUse", [])
    if not isinstance(groups, list):
        raise ValueError("PreToolUse must be a list")
    destination = config / "hooks" / "destructive_guard.py"
    command = shlex.join([sys.executable, str(destination)])
    handler = {"type": "command", "command": command, "timeout": 10}
    if not any(isinstance(group, dict) and group.get("matcher") == "Bash" and handler in group.get("hooks", []) for group in groups):
        groups.append({"matcher": "Bash", "hooks": [handler]})
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).with_name("destructive_guard.py"), destination)
    payload = (json.dumps(data, indent=2) + "\n").encode()
    if payload != original:
        if original is not None:
            fd, backup = tempfile.mkstemp(prefix="settings.json.before-destructive-guard-", dir=config)
            with os.fdopen(fd, "wb") as file:
                file.write(original)
            print(f"Existing settings backed up to {backup}")
        fd, temporary = tempfile.mkstemp(prefix=".settings-", dir=config)
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(payload)
            os.replace(temporary, settings)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    print(f"Installed {destination}. Start a new Claude Code session to load the hook.")


if __name__ == "__main__":
    try:
        install()
    except (OSError, ValueError, TypeError) as error:
        sys.exit(f"Installation failed: {error}")
