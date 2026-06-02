#!/usr/bin/env python3
"""Install the destructive Bash guard into ~/.claude/hooks."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


HOOK_NAME = "block_destructive_bash.py"


def command_string(args: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(args)
    return " ".join(shlex.quote(arg) for arg in args)


def hook_command(destination: Path) -> str:
    return command_string([sys.executable, str(destination)])


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object at the top level.")
    return data


def merge_hook(settings: dict[str, Any], command: str) -> dict[str, Any]:
    hooks_value = settings.get("hooks")
    if hooks_value is None:
        hooks: dict[str, Any] = {}
        settings["hooks"] = hooks
    elif isinstance(hooks_value, dict):
        hooks = hooks_value
    else:
        raise SystemExit('Expected "hooks" in settings.json to be a JSON object.')

    pre_tool_use_value = hooks.get("PreToolUse")
    if pre_tool_use_value is None:
        pre_tool_use: list[Any] = []
        hooks["PreToolUse"] = pre_tool_use
    elif isinstance(pre_tool_use_value, list):
        pre_tool_use = pre_tool_use_value
    else:
        raise SystemExit('Expected "hooks.PreToolUse" in settings.json to be a list.')

    hook_entry = {"type": "command", "command": command}

    for existing in pre_tool_use:
        if not isinstance(existing, dict) or existing.get("matcher") != "Bash":
            continue
        existing_hooks_value = existing.get("hooks")
        if existing_hooks_value is None:
            existing_hooks: list[Any] = []
            existing["hooks"] = existing_hooks
        elif isinstance(existing_hooks_value, list):
            existing_hooks = existing_hooks_value
        else:
            raise SystemExit('Expected existing Bash "hooks" in settings.json to be a list.')
        if any(hook == hook_entry for hook in existing_hooks):
            return settings
        existing_hooks.append(hook_entry)
        return settings

    pre_tool_use.append({"matcher": "Bash", "hooks": [hook_entry]})
    return settings


def reject_symlink(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return
    if stat.S_ISLNK(mode):
        raise SystemExit(f"Refusing to overwrite symlinked hook path: {path}")


def fsync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(directory, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def fsync_file(path: Path) -> None:
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def install_hook_file(source: Path, destination: Path) -> None:
    reject_symlink(destination)
    fd, temp_name = tempfile.mkstemp(prefix=f".{HOOK_NAME}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        shutil.copy2(source, temp_path)
        if os.name != "nt":
            temp_path.chmod(0o755)
            fsync_file(temp_path)
        reject_symlink(destination)
        os.replace(temp_path, destination)
        fsync_directory(destination.parent)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def write_settings_atomic(settings_path: Path, settings: dict[str, Any]) -> None:
    try:
        existing_mode = settings_path.stat().st_mode & 0o777
    except FileNotFoundError:
        existing_mode = 0o600

    fd, temp_name = tempfile.mkstemp(prefix=".settings.", suffix=".tmp", dir=settings_path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if os.name != "nt":
            temp_path.chmod(existing_mode)
        os.replace(temp_path, settings_path)
        fsync_directory(settings_path.parent)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main() -> int:
    source = Path(__file__).with_name(HOOK_NAME)
    claude_dir = Path.home() / ".claude"
    hook_dir = claude_dir / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)

    destination = hook_dir / HOOK_NAME
    install_hook_file(source, destination)

    settings_path = claude_dir / "settings.json"
    settings = merge_hook(load_settings(settings_path), hook_command(destination))
    write_settings_atomic(settings_path, settings)

    print(f"Installed {destination}")
    print(f"Updated {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
