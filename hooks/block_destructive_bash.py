#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RM_RF_RE = re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b|\brm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b")
DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
GIT_FORCE_PUSH_RE = re.compile(r"\bgit\s+push\b(?:(?![;&|]).)*(?:--force(?:-with-lease)?|-f)\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)

HOOK_NAME = "block_destructive_bash.py"


def classify_command(command: str) -> str | None:
    """Return the blocking reason for a command, or None if it should run."""
    checks = [
        (RM_RF_RE, "rm -rf recursively deletes files and is blocked by policy"),
        (GIT_FORCE_PUSH_RE, "git push --force can rewrite shared history and is blocked by policy"),
    ]

    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    if is_read_only_search_command(command):
        return None

    sql_checks = [
        (DROP_TABLE_RE, "DROP TABLE can destroy database schema/data and is blocked by policy"),
        (TRUNCATE_RE, "TRUNCATE can erase table contents and is blocked by policy"),
    ]
    for pattern, reason in sql_checks:
        if pattern.search(command):
            return reason

    delete_match = DELETE_FROM_RE.search(command)
    if delete_match and not delete_statement_has_where(command, delete_match.end()):
        return "DELETE FROM without a WHERE clause can erase table contents and is blocked by policy"

    return None


def is_read_only_search_command(command: str) -> bool:
    """Avoid blocking harmless searches for dangerous SQL strings."""
    if any(delimiter in command for delimiter in (";", "&&", "||", "|", "`", "$(")):
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if not tokens:
        return False
    executable = Path(tokens[0]).name
    return executable in {"grep", "rg", "ag"}


def delete_statement_has_where(command: str, start: int) -> bool:
    """Check whether the DELETE FROM statement segment has a WHERE clause."""
    remainder = command[start:]
    terminators = [idx for idx in (remainder.find(";"), remainder.find("&&"), remainder.find("||"), remainder.find("|")) if idx != -1]
    statement = remainder[: min(terminators)] if terminators else remainder
    return bool(WHERE_RE.search(statement))


def project_path(payload: dict[str, Any]) -> str:
    """Extract the best available project path from hook input or environment."""
    candidates = [
        os.environ.get("CLAUDE_PROJECT_DIR"),
        payload.get("cwd"),
        payload.get("project_dir"),
        payload.get("workspace", {}).get("current_dir") if isinstance(payload.get("workspace"), dict) else None,
        os.getcwd(),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return "unknown"


def log_blocked(command: str, path: str) -> None:
    """Append a blocked attempt to the log file."""
    log_path = Path(os.environ.get("CLAUDE_BLOCKED_LOG", "~/.claude/hooks/blocked.log")).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": path,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def deny(reason: str, command: str, path: str) -> dict[str, Any]:
    """Build a Claude Code PreToolUse denial response."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command: {reason}. "
                f"Project path: {path}. Command: {command}"
            ),
        }
    }


def handle(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Return a denial payload for blocked commands; None allows execution."""
    if payload.get("tool_name") != "Bash":
        return None

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command")
    if not isinstance(command, str):
        return None

    reason = classify_command(command)
    if not reason:
        return None

    path = project_path(payload)
    log_blocked(command, path)
    return deny(reason, command, path)


def install() -> None:
    """Install this hook under ~/.claude/hooks and update ~/.claude/settings.json."""
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    target = hooks_dir / HOOK_NAME
    source = Path(__file__).resolve()
    if source != target:
        shutil.copy2(source, target)
    mode = target.stat().st_mode
    target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        with settings_path.open("r", encoding="utf-8") as handle:
            settings = json.load(handle)
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f"{sys.executable} {target}"
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }

    existing_commands = {
        hook.get("command")
        for group in pre_tool_use
        if isinstance(group, dict)
        for hook in group.get("hooks", [])
        if isinstance(hook, dict)
    }
    if command not in existing_commands:
        pre_tool_use.append(entry)

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed {target}")
    print(f"Updated {settings_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Block destructive Bash commands in Claude Code.")
    parser.add_argument("--install", action="store_true", help="Install the hook into ~/.claude/hooks.")
    args = parser.parse_args(argv)

    if args.install:
        install()
        return 0

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON input: {exc}", file=sys.stderr)
        return 1

    response = handle(payload)
    if response is not None:
        print(json.dumps(response, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
