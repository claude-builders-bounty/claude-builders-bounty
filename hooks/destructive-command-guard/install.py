#!/usr/bin/env python3
"""Install the guard without discarding existing Claude Code settings."""

import argparse
import copy
import json
import os
from pathlib import Path
import sys
import tempfile


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("settings.json contains a duplicate key: {!r}".format(key))
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("settings.json contains an invalid JSON number: {}".format(value))


def _validated_settings(raw):
    settings = json.loads(
        raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_invalid_constant,
    )
    if not isinstance(settings, dict):
        raise ValueError("settings.json must contain a JSON object")
    if "hooks" not in settings:
        return settings
    hooks = settings["hooks"]
    if not isinstance(hooks, dict):
        raise ValueError("settings.json: hooks must be an object")
    if "PreToolUse" not in hooks:
        return settings
    groups = hooks["PreToolUse"]
    if not isinstance(groups, list):
        raise ValueError("settings.json: hooks.PreToolUse must be an array")
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("settings.json: each PreToolUse entry must be an object")
        if "matcher" in group and not isinstance(group["matcher"], str):
            raise ValueError("settings.json: a hook matcher must be a string")
        if not isinstance(group.get("hooks"), list):
            raise ValueError("settings.json: each PreToolUse entry needs a hooks array")
        if any(not isinstance(handler, dict) for handler in group["hooks"]):
            raise ValueError("settings.json: each hook handler must be an object")
    return settings


def _merge_settings(settings, target):
    result = copy.deepcopy(settings)
    groups = result.setdefault("hooks", {}).setdefault("PreToolUse", [])
    handler = {
        "type": "command",
        "command": sys.executable,
        "args": [str(target)],
    }
    # The script path identifies this installation even if Python has moved.
    for group in groups:
        if group.get("matcher") != "Bash":
            continue
        for existing in group["hooks"]:
            if existing.get("type") == "command" and existing.get("args") == handler["args"]:
                existing.update(handler)
                return result
    groups.append({"matcher": "Bash", "hooks": [handler]})
    return result


def _atomic_write(path, data):
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _backup_settings(path, original):
    # Exclusive creation preserves every older backup, including symlinks.
    index = 0
    while True:
        suffix = ".bak" if index == 0 else ".bak.{}".format(index)
        candidate = path.with_name(path.name + suffix)
        try:
            fd = os.open(str(candidate), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            index += 1
            continue
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            candidate.unlink()
            raise
        return candidate


def install(claude_dir):
    claude_dir = claude_dir.expanduser().absolute()
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"
    target = hooks_dir / "destructive_command_guard.py"
    source = Path(__file__).resolve().with_name("guard.py")

    # Validate everything readable before creating directories or replacing files.
    payload = source.read_bytes()
    if not payload:
        raise ValueError("guard.py is empty; installation cancelled")
    for directory in (claude_dir, hooks_dir):
        if directory.exists() and not directory.is_dir():
            raise ValueError("Expected a directory: {}".format(directory))
    for path in (settings_path, target):
        if path.is_symlink():
            raise ValueError("Refusing to replace a symbolic link: {}".format(path))
        if path.exists() and not path.is_file():
            raise ValueError("Expected a regular file: {}".format(path))
    original = settings_path.read_bytes() if settings_path.exists() else None
    settings = _validated_settings(original) if original is not None else {}
    merged = _merge_settings(settings, target)
    settings_changed = original is None or merged != settings
    updated = (json.dumps(merged, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    claude_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    hooks_dir.mkdir(exist_ok=True, mode=0o700)
    backup = None
    if settings_changed and original is not None:
        backup = _backup_settings(settings_path, original)
    if not target.exists() or target.read_bytes() != payload:
        _atomic_write(target, payload)
    if settings_changed:
        _atomic_write(settings_path, updated)
    return target, settings_path, backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--claude-dir", type=Path, default=Path.home() / ".claude",
        help="Claude configuration directory (default: ~/.claude)",
    )
    args = parser.parse_args()
    try:
        target, settings_path, backup = install(args.claude_dir)
    except (OSError, ValueError, UnicodeError) as error:
        print("Installation failed: {}".format(error), file=sys.stderr)
        return 1
    print("Installed {}".format(target))
    print("Configured Bash PreToolUse hook in {}".format(settings_path))
    if backup is not None:
        print("Saved previous settings to {}".format(backup))
    return 0


if __name__ == "__main__":
    sys.exit(main())
