#!/usr/bin/env python3
"""Install the local hook into Claude Code without dependencies or downloads."""

import json
import os
from pathlib import Path
import shlex
import stat
import sys
import uuid


class InstallError(Exception):
    """A local configuration cannot safely be updated."""


def _directory(path):
    """Create private directories; never follow the final directory symlink."""
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    try:
        return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        raise InstallError("Expected a real directory: {}".format(path)) from exc


def _read_file(directory, name):
    """Use directory handles and O_NOFOLLOW to avoid symlink replacement races."""
    try:
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise InstallError("Expected a regular file, not a link or special file: " + name)
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
    except OSError as exc:
        raise InstallError("Cannot safely open " + name) from exc
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise InstallError("Expected a regular file: " + name)
        return handle.read()


def _write_new(directory, name, content):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=directory)
    with os.fdopen(fd, "wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _replace(directory, name, content):
    """Write privately, then atomically replace the destination in the same dir."""
    temporary = ".{}.{}.tmp".format(name, uuid.uuid4().hex)
    try:
        _write_new(directory, temporary, content)
        os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InstallError("Duplicate settings key: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise InstallError("Non-standard JSON constant in settings.json: " + value)


def _settings(content):
    if content is None:
        return {}
    try:
        result = json.loads(content.decode("utf-8"), object_pairs_hook=_unique_object,
                            parse_constant=_reject_constant)
    except (ValueError, UnicodeError) as exc:
        raise InstallError("settings.json is not valid UTF-8 JSON") from exc
    if not isinstance(result, dict):
        raise InstallError("settings.json must contain an object")
    hooks = result.get("hooks", {})
    if not isinstance(hooks, dict):
        raise InstallError("settings.json hooks must be an object")
    entries = hooks.get("PreToolUse", [])
    if not isinstance(entries, list):
        raise InstallError("settings.json hooks.PreToolUse must be an array")
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
            raise InstallError("Every PreToolUse entry must have a hooks array")
        if "matcher" in entry and not isinstance(entry["matcher"], str):
            raise InstallError("PreToolUse matcher must be a string")
        if not all(isinstance(hook, dict) for hook in entry["hooks"]):
            raise InstallError("PreToolUse hooks must contain objects")
    return result


def install():
    """Preserve unrelated settings and register the hook at most once."""
    source_dir = Path(__file__).resolve().parent / "hooks"
    # Read all source bytes before making any changes in the user's home.
    source_fd = os.open(source_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        source = _read_file(source_fd, "block_destructive_commands.py")
    finally:
        os.close(source_fd)
    if source is None:
        raise InstallError("Missing hooks/block_destructive_commands.py")

    claude_dir = Path.home().absolute() / ".claude"
    claude_fd = _directory(claude_dir)
    hooks_fd = None
    try:
        previous = _read_file(claude_fd, "settings.json")
        settings = _settings(previous)
        # Anchor the child directory open to the already checked parent handle.
        try:
            os.mkdir("hooks", 0o700, dir_fd=claude_fd)
        except FileExistsError:
            pass
        try:
            hooks_fd = os.open("hooks", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                               dir_fd=claude_fd)
        except OSError as exc:
            raise InstallError("Expected a real .claude/hooks directory") from exc
        installed = _read_file(hooks_fd, "block_destructive_commands.py")

        destination = claude_dir / "hooks" / "block_destructive_commands.py"
        command = "{} {}".format(shlex.quote(sys.executable), shlex.quote(str(destination)))
        entries = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
        registered = any(
            entry.get("matcher") == "Bash" and any(
                hook.get("type") == "command" and hook.get("command") == command
                for hook in entry["hooks"]
            )
            for entry in entries
        )
        if not registered:
            entries.append({"matcher": "Bash", "hooks": [{"type": "command", "command": command}]})

        # Preserve the exact original bytes before the first settings mutation.
        if not registered and previous is not None:
            backup = "settings.json.backup-" + uuid.uuid4().hex
            _write_new(claude_fd, backup, previous)
            print("Backed up settings to " + str(claude_dir / backup))
        if installed != source:
            _replace(hooks_fd, "block_destructive_commands.py", source)
        if not registered:
            content = (json.dumps(settings, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            _replace(claude_fd, "settings.json", content)
        print("Installed local Bash safety hook: " + str(destination))
    finally:
        if hooks_fd is not None:
            os.close(hooks_fd)
        os.close(claude_fd)


if __name__ == "__main__":
    try:
        install()
    except (InstallError, OSError) as error:
        print("Install failed: {}".format(error), file=sys.stderr)
        sys.exit(1)
