#!/usr/bin/env python3
"""Install only when invoked by the user; retain unrelated settings and hooks."""
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile


def main():
    root = Path.home() / ".claude"
    settings = root / "settings.json"
    data = json.loads(settings.read_text()) if settings.exists() else {}
    if not isinstance(data, dict):
        raise ValueError("Existing settings must be an object")
    entries = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if not isinstance(entries, list):
        raise ValueError("Existing PreToolUse settings must be a list")
    source = Path(__file__).with_name("destructive_guard.py").read_bytes()
    destination = root / "hooks" / "destructive_guard.py"
    if destination.is_symlink() or (destination.exists() and destination.read_bytes() != source):
        raise ValueError("Destination already exists with different content; refusing to overwrite it")
    command = shlex.join([sys.executable, str(destination)])
    entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": command}]}
    if entry not in entries:
        entries.append(entry)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source)
    destination.chmod(0o700)
    fd, temporary = tempfile.mkstemp(prefix="settings-", dir=root)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, settings)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"Installed hook at {destination}; existing settings retained.")


if __name__ == "__main__":
    main()
