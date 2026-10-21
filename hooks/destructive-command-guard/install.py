#!/usr/bin/env python3
"""Install this hook without replacing other Claude Code settings or hooks."""

import argparse
import json
import os
from pathlib import Path
import shlex
import stat
import sys
import tempfile


def atomic_write(path, content, mode):
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def backup_once(path, content, mode):
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    except FileExistsError:
        return
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def install(config_dir):
    config_dir = config_dir.expanduser().resolve()
    settings_path = config_dir / "settings.json"
    hooks_dir = config_dir / "hooks"
    destination = hooks_dir / "destructive-command-guard.py"
    for path in (settings_path, destination):
        if path.is_symlink():
            raise ValueError("Refusing to replace a symbolic link: " + str(path))

    original = settings_path.read_bytes() if settings_path.exists() else None
    settings = json.loads(original) if original is not None else {}
    if not isinstance(settings, dict):
        raise ValueError("settings.json must contain a JSON object")
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must be an object")
    entries = hooks.setdefault("PreToolUse", [])
    if not isinstance(entries, list):
        raise ValueError("hooks.PreToolUse must be an array")
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
            raise ValueError("Each existing PreToolUse entry must contain a hooks array")
        if any(not isinstance(handler, dict) for handler in entry["hooks"]):
            raise ValueError("Existing hook handlers must be objects")

    command = shlex.join([
        sys.executable, str(destination), "--hooks-dir", str(hooks_dir)
    ])
    handler = {"type": "command", "command": command, "timeout": 5}
    owned_entry = {"matcher": "Bash", "hooks": [handler]}
    if owned_entry not in entries:
        entries.append(owned_entry)
    content = (json.dumps(settings, indent=2, ensure_ascii=False) + "\n").encode()
    source = Path(__file__).with_name("guard.py").read_bytes()
    mode = stat.S_IMODE(settings_path.stat().st_mode) if original is not None else 0o600

    hooks_dir.mkdir(parents=True, exist_ok=True)
    # A concurrent edit must not be silently overwritten.
    current = settings_path.read_bytes() if settings_path.exists() else None
    if current != original:
        raise ValueError("settings.json changed during installation; retry after reviewing it")
    if original is not None and original != content:
        backup_once(config_dir / "settings.json.before-destructive-guard", original, mode)
    if destination.exists() and destination.read_bytes() != source:
        backup_once(hooks_dir / "destructive-command-guard.py.previous",
                    destination.read_bytes(), stat.S_IMODE(destination.stat().st_mode))
    if not destination.exists() or destination.read_bytes() != source:
        atomic_write(destination, source, 0o700)
    if original != content:
        atomic_write(settings_path, content, mode)
    print("Installed Bash PreToolUse hook in " + str(settings_path))
    print("Blocked attempts are logged to " + str(hooks_dir / "blocked.log"))
    print("Restart Claude Code or reload hooks with /hooks to apply the configuration.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path,
                        default=Path.home() / ".claude",
                        help="Claude settings directory (default: ~/.claude)")
    args = parser.parse_args()
    try:
        install(args.config_dir)
    except (OSError, ValueError) as error:
        print("Installation failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
