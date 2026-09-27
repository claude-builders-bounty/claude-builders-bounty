#!/usr/bin/env python3
"""Install the Bash PreToolUse guard without replacing existing user settings."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import sys
import tempfile


def _read_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read valid JSON from {path}.") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected an object in {path}.")
    return value


def _handler_for(script: Path) -> dict:
    return {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": sys.executable,
                "args": [str(script)],
            }
        ],
    }


def _write_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    old_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, temp_name = tempfile.mkstemp(
        prefix=".settings-", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(settings, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_name, old_mode)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def install(home: Path | None = None) -> Path:
    home = home or Path.home()
    config_dir = home / ".claude"
    settings_path = config_dir / "settings.json"
    hooks = config_dir / "hooks"
    script_path = hooks / "destructive_command_guard.py"
    source_path = Path(__file__).with_name("guard.py")

    settings = _read_settings(settings_path)
    hook_config = settings.setdefault("hooks", {})
    if not isinstance(hook_config, dict):
        raise RuntimeError(f"The hooks setting in {settings_path} must be an object.")
    pre_tool_use = hook_config.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise RuntimeError(f"PreToolUse in {settings_path} must be an array.")

    handler = _handler_for(script_path)
    if handler not in pre_tool_use:
        pre_tool_use.append(handler)

    existing = script_path.read_bytes() if script_path.exists() else None
    source = source_path.read_bytes()
    if existing is not None and existing != source:
        raise RuntimeError(
            f"Refusing to replace different file contents at {script_path}; move it aside first."
        )

    hooks.mkdir(mode=0o700, parents=True, exist_ok=True)
    if existing is None:
        fd, temp_name = tempfile.mkstemp(
            prefix=".destructive_command_guard.", suffix=".tmp", dir=hooks
        )
        os.close(fd)
        temp_path = Path(temp_name)
        try:
            temp_path.write_bytes(source)
            temp_path.chmod(0o700)
            os.replace(temp_path, script_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    _write_settings(settings_path, settings)
    return script_path


def main() -> int:
    try:
        path = install()
    except (OSError, RuntimeError) as exc:
        print(
            f"Installation stopped without replacing settings: {exc}", file=sys.stderr
        )
        return 1
    print(
        f"Installed the Bash guard at {path}. Review ~/.claude/settings.json and restart Claude Code."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
