#!/usr/bin/env python3
"""Install the destructive-command hook without overwriting user settings."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


_COMMAND = "python3 ~/.claude/hooks/block_destructive.py"


def _settings_with_hook(settings: dict[str, Any]) -> dict[str, Any]:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings['hooks'] must be an object")
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise ValueError("settings['hooks']['PreToolUse'] must be an array")

    for group in pre_tool_use:
        if not isinstance(group, dict):
            continue
        for handler in group.get("hooks", []):
            if isinstance(handler, dict) and handler.get("command") == _COMMAND:
                return settings

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": _COMMAND}],
        }
    )
    return settings


def _write_json_atomically(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(value, output, indent=2, ensure_ascii=False)
            output.write("\n")
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def install(*, home: Path | None = None, source_dir: Path | None = None) -> Path:
    """Install the hook and merge its PreToolUse entry into settings.json."""

    target_home = Path(home) if home is not None else Path.home() / ".claude"
    source = Path(source_dir) if source_dir is not None else Path(__file__).parent
    target_hooks = target_home / "hooks"
    target_hooks.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "block_destructive.py", target_hooks / "block_destructive.py")

    settings_path = target_home / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Cannot read {settings_path}: {error}") from error
        if not isinstance(settings, dict):
            raise ValueError("settings.json must contain a JSON object")
    else:
        settings = {}

    _write_json_atomically(settings_path, _settings_with_hook(settings))
    return target_hooks / "block_destructive.py"


if __name__ == "__main__":
    installed = install()
    print(f"Installed destructive-command hook at {installed}")
