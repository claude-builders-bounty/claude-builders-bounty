#!/usr/bin/env python3
"""Install the destructive-command hook without overwriting other settings."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import shlex
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
HOOK_NAME = "destructive_command_guard.py"


def _command_part(value: str) -> str:
    """Quote one interpreter or path operand for the host shell."""

    if os.name == "nt":
        return f'"{value}"'
    return shlex.quote(value)


def hook_command(home: Path) -> str:
    """Return the executable hook command for this machine's settings file.

    The legacy ``python3 ~/.claude/...`` command is convenient on POSIX, but
    often does not resolve on Windows.  The installer is per-user and per-host,
    so preserving the interpreter that successfully ran it is more reliable
    than assuming a shell alias exists later.
    """

    hook_path = home / ".claude" / "hooks" / HOOK_NAME
    return f"{_command_part(sys.executable)} {_command_part(str(hook_path))}"


def _hook_entry(command: str) -> dict[str, str]:
    return {"type": "command", "command": command}


def _write_settings_atomically(settings_path: Path, settings: dict[str, object]) -> None:
    """Replace settings.json without risking a partially written config."""

    mode = stat.S_IMODE(settings_path.stat().st_mode) if settings_path.exists() else None
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=settings_path.parent,
            prefix=f".{settings_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(json.dumps(settings, indent=2) + "\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        if mode is not None:
            os.chmod(temporary_path, mode)
        os.replace(temporary_path, settings_path)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def install(home: Path | None = None) -> Path:
    home = home or Path.home()
    settings_path = home / ".claude" / "settings.json"
    command = hook_command(home)
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Cannot read {settings_path}: {exc}") from exc
        if not isinstance(settings, dict):
            raise RuntimeError(f"Expected a JSON object in {settings_path}")
    else:
        settings = {}
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise RuntimeError("The existing hooks setting is not a JSON object")
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise RuntimeError("The existing PreToolUse setting is not a JSON array")
    for matcher in pre_tool_use:
        if not isinstance(matcher, dict) or matcher.get("matcher") != "Bash":
            continue
        nested = matcher.get("hooks", [])
        if isinstance(nested, list) and any(
            isinstance(entry, dict) and entry.get("command") == command for entry in nested
        ):
            break
    else:
        pre_tool_use.append({"matcher": "Bash", "hooks": [_hook_entry(command)]})

    hooks_dir = home / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    destination = hooks_dir / HOOK_NAME
    shutil.copy2(ROOT / HOOK_NAME, destination)
    destination.chmod(destination.stat().st_mode | 0o111)
    _write_settings_atomically(settings_path, settings)
    return destination


if __name__ == "__main__":
    try:
        installed = install()
    except (OSError, RuntimeError) as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Installed {installed} and updated ~/.claude/settings.json")
