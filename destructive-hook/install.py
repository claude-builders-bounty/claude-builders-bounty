"""Install locally without replacing existing Claude Code settings."""
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile


def install():
    home = Path.home() / ".claude"
    hooks = home / "hooks"
    settings = home / "settings.json"
    old = settings.read_bytes() if settings.exists() else None
    data = json.loads(old) if old else {}
    entries = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if not isinstance(entries, list):
        raise ValueError("PreToolUse must be a list; no settings changed")
    target = hooks / "destructive-guard.py"
    # Forward slashes work in Git Bash, including Windows paths with spaces.
    command = shlex.join([Path(sys.executable).as_posix(), target.as_posix()])
    entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": command}]}
    if entry not in entries:
        entries.append(entry)
    hooks.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or settings.is_symlink():
        raise ValueError("Refusing symlink install targets")
    shutil.copyfile(Path(__file__).with_name("guard.py"), target)
    new = (json.dumps(data, indent=2) + "\n").encode()
    if old == new:
        return
    if old is not None:
        fd, backup = tempfile.mkstemp(prefix="settings.json.backup-", dir=home)
        with os.fdopen(fd, "wb") as stream:
            stream.write(old)
    fd, temp = tempfile.mkstemp(prefix=".settings-", dir=home)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(new)
        os.replace(temp, settings)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


if __name__ == "__main__":
    install()
