#!/usr/bin/env python3
"""Install the hook into the current user's Claude Code configuration."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
import sys
import tempfile
from pathlib import Path


def safe_directory(path: Path) -> None:
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise RuntimeError(f"refusing unsafe configuration directory: {path}")


def read_settings(path: Path) -> dict:
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise RuntimeError("refusing to read an unsafe Claude settings file") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError("refusing to replace a non-regular Claude settings file")
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = -1
            value = json.load(stream)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise RuntimeError("could not read valid ~/.claude/settings.json; no changes made") from exc
    finally:
        if fd >= 0:
            os.close(fd)
    if not isinstance(value, dict):
        raise RuntimeError("settings.json must contain a JSON object; no changes made")
    return value


def atomic_write(path: Path, text: str, existing_mode: int | None) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=".settings-", dir=path.parent)
    temp = Path(temp_name)
    try:
        os.fchmod(fd, existing_mode if existing_mode is not None else 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except Exception:
        try:
            temp.unlink()
        except OSError:
            pass
        raise


def install(home: Path | None = None) -> Path:
    home = home or Path.home()
    claude_dir = home / ".claude"
    hooks_dir = claude_dir / "hooks"
    safe_directory(claude_dir)
    safe_directory(hooks_dir)

    source = Path(__file__).resolve().with_name("command_guard.py")
    if not source.is_file():
        raise RuntimeError("command_guard.py is missing; no changes made")
    target = hooks_dir / "command_guard.py"
    content = source.read_bytes()
    settings_path = claude_dir / "settings.json"
    try:
        info = settings_path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise RuntimeError("refusing to replace a non-regular Claude settings file")
        old_mode = stat.S_IMODE(info.st_mode)
    except FileNotFoundError:
        old_mode = None
    settings = read_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise RuntimeError("settings.json has a non-object 'hooks' field; no configuration changed")
    pre_tool = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool, list):
        raise RuntimeError("settings.json has a non-list 'hooks.PreToolUse' field; no configuration changed")

    for group in pre_tool:
        if not isinstance(group, dict) or not isinstance(group.get("hooks", []), list):
            raise RuntimeError("settings.json has an invalid PreToolUse hook group; no changes made")

    command = shlex.quote(str(target))
    existing_handlers = [
        handler
        for group in pre_tool
        if group.get("matcher") == "Bash"
        for handler in group.get("hooks", [])
        if isinstance(handler, dict)
        and handler.get("type") == "command"
        and handler.get("command") == command
    ]
    settings_changed = not existing_handlers
    for handler in existing_handlers:
        if handler.get("onFailure") != "block":
            handler["onFailure"] = "block"
            settings_changed = True

    # Validate settings before writing the hook, so malformed user settings
    # never leave a partial installation behind.
    try:
        existing_fd = os.open(
            target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
        )
    except FileNotFoundError:
        existing_fd = None
    except OSError as exc:
        raise RuntimeError("refusing to read an unsafe hook path") from exc
    created_target = False
    if existing_fd is not None:
        try:
            info = os.fstat(existing_fd)
            if not stat.S_ISREG(info.st_mode):
                raise RuntimeError("refusing to overwrite an unsafe hook path")
            chunks = []
            while True:
                chunk = os.read(existing_fd, 64 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if b"".join(chunks) != content:
                raise RuntimeError("a different command_guard.py already exists; move it aside before installing")
            os.fchmod(existing_fd, 0o700)
        finally:
            os.close(existing_fd)
    else:
        try:
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o700)
            created_target = True
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            try:
                target.unlink()
            except OSError:
                pass
            raise

    if not existing_handlers:
        pre_tool.append(
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": command,
                        "onFailure": "block",
                    }
                ],
            }
        )
    if settings_changed:
        try:
            atomic_write(settings_path, json.dumps(settings, indent=2, ensure_ascii=False) + "\n", old_mode)
        except Exception:
            if created_target:
                try:
                    target.unlink()
                except OSError:
                    pass
            raise
    return settings_path


if __name__ == "__main__":
    try:
        path = install()
    except (OSError, RuntimeError) as exc:
        print(f"Install failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Installed Claude Code Bash guard in {path}")
