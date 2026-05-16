#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any


HOOK_COMMAND = "python3 ~/.claude/hooks/block_destructive_bash.py"


BLOCK_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?is)(^|[;&|]\s*|\s)(?:sudo\s+)?rm\s+(?:(?:-[^\s]*r[^\s]*f[^\s]*|-"
            r"[^\s]*f[^\s]*r[^\s]*)|(?=.*--recursive)(?=.*--force))\b"
        ),
        "Recursive forced deletion is blocked (`rm -rf` / `rm -fr`).",
    ),
    (
        re.compile(r"(?is)\bdrop\s+table\b"),
        "Destructive SQL schema deletion is blocked (`DROP TABLE`).",
    ),
    (
        re.compile(r"(?is)\btruncate(?:\s+table)?\b"),
        "Destructive SQL truncation is blocked (`TRUNCATE`).",
    ),
    (
        re.compile(r"(?is)\bgit\s+push\b(?=.*(?:--force(?:-with-lease)?|\s-f(?:\s|$)))"),
        "Force-pushing is blocked (`git push --force`).",
    ),
)


DELETE_FROM_PATTERN = re.compile(r"(?is)\bdelete\s+from\b")
WHERE_PATTERN = re.compile(r"(?is)\bwhere\b")


def log_path() -> pathlib.Path:
    override = os.environ.get("CLAUDE_HOOK_LOG")
    if override:
        return pathlib.Path(override).expanduser()
    return pathlib.Path.home() / ".claude" / "hooks" / "blocked.log"


def normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command).strip()


def delete_without_where_reason(command: str) -> str | None:
    for match in DELETE_FROM_PATTERN.finditer(command):
        statement = command[match.start() :]
        statement = statement.split(";", 1)[0]
        if not WHERE_PATTERN.search(statement):
            return "Destructive SQL delete without WHERE is blocked (`DELETE FROM` without `WHERE`)."
    return None


def blocked_reason(command: str) -> str | None:
    normalized = normalize_command(command)
    if not normalized:
        return None

    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(normalized):
            return reason

    return delete_without_where_reason(normalized)


def append_block_log(command: str, project_path: str, reason: str) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "attempted_command": command,
        "reason": reason,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def hook_main(input_data: dict[str, Any]) -> int:
    if input_data.get("tool_name") != "Bash":
        return 0

    tool_input = input_data.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = blocked_reason(command)
    if not reason:
        return 0

    project_path = (
        str(input_data.get("cwd") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    append_block_log(command, project_path, reason)

    print(
        "Blocked destructive Bash command.\n"
        f"Reason: {reason}\n"
        f"Project path: {project_path}\n"
        f"Attempted command: {command}\n"
        "Use a safer, scoped command or ask the user for explicit confirmation.",
        file=sys.stderr,
    )
    return 2


def install_hook() -> int:
    settings_path = pathlib.Path.home() / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        with settings_path.open("r", encoding="utf-8") as handle:
            try:
                settings = json.load(handle)
            except json.JSONDecodeError as exc:
                print(f"Cannot parse {settings_path}: {exc}", file=sys.stderr)
                return 1
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    matcher_entry = None
    for entry in pre_tool_use:
        if entry.get("matcher") == "Bash":
            matcher_entry = entry
            break

    if matcher_entry is None:
        matcher_entry = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(matcher_entry)

    commands = matcher_entry.setdefault("hooks", [])
    if not any(hook.get("command") == HOOK_COMMAND for hook in commands):
        commands.append({"type": "command", "command": HOOK_COMMAND})

    backup_path = settings_path.with_suffix(".json.bak")
    if settings_path.exists() and not backup_path.exists():
        backup_path.write_text(settings_path.read_text(encoding="utf-8"), encoding="utf-8")

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed Claude Code Bash guard in {settings_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Register this hook in ~/.claude/settings.json")
    args = parser.parse_args()

    if args.install:
        return install_hook()

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON input: {exc}", file=sys.stderr)
        return 1

    return hook_main(input_data)


if __name__ == "__main__":
    raise SystemExit(main())

