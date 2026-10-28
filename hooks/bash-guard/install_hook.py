#!/usr/bin/env python3
"""Install the Bash guard without replacing unrelated Claude Code settings."""

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


def atomic_write(path, data, mode):
    fd, temporary = tempfile.mkstemp(prefix=".bash-guard-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def command_line(executable, script):
    """Quote both paths for the shell Claude Code uses to run hook commands."""
    if os.name == "nt":
        return subprocess.list2cmdline([executable, "-B", script])
    return " ".join(shlex.quote(part) for part in (executable, "-B", script))


def install(config):
    config = config.expanduser().resolve()
    settings_path = config / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    if not isinstance(settings, dict):
        raise ValueError("settings.json must contain an object")
    if settings.get("disableAllHooks"):
        raise ValueError("disableAllHooks is enabled; no settings changed")
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must contain an object")
    entries = hooks.setdefault("PreToolUse", [])
    if not isinstance(entries, list) or any(not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list) for entry in entries):
        raise ValueError("PreToolUse must contain matcher objects with hook lists")
    destination = config / "hooks" / "bash_guard.py"
    executable = str(Path(sys.executable).resolve())
    # The long-standing single-string form works on every Claude Code version.
    handler = {"type": "command", "command": command_line(executable, str(destination)), "timeout": 10}
    # Replace only this installed script's handler; retain neighboring handlers.
    remaining = []
    for entry in entries:
        kept = [item for item in entry["hooks"] if not (
            isinstance(item, dict) and item.get("type") == "command"
            and item.get("command") == handler["command"])]
        if kept or not entry["hooks"]:
            remaining.append({**entry, "hooks": kept})
    remaining.append({"matcher": "Bash", "hooks": [handler]})
    hooks["PreToolUse"] = remaining
    source = Path(__file__).resolve().parent / "bash_guard.py"
    data = source.read_bytes()
    serialized = (json.dumps(settings, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    config.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.parent.mkdir(exist_ok=True, mode=0o700)
    atomic_write(destination, data, 0o700)
    old_mode = settings_path.stat().st_mode & 0o777 if settings_path.exists() else 0o600
    atomic_write(settings_path, serialized, old_mode)
    print(f"Installed Bash guard: {destination}")
    print(f"Registered PreToolUse/Bash in {settings_path}. Restart Claude Code to reload hooks.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")))
    args = parser.parse_args()
    try:
        install(args.config_dir)
    except (OSError, ValueError) as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
