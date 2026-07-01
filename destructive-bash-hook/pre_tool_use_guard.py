#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import sys
from typing import Any, Optional


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b(?P<body>.*?)(?:;|$)", re.IGNORECASE | re.DOTALL)
RM_RF_RE = re.compile(r"(?:^|[;&|]\s*)rm\s+-[A-Za-z]*r[A-Za-z]*f|(?:^|[;&|]\s*)rm\s+-[A-Za-z]*f[A-Za-z]*r")


def _read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"tool_input": {"command": raw}}
    return payload if isinstance(payload, dict) else {}


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value

    nested_input = payload.get("input")
    if isinstance(nested_input, dict):
        value = nested_input.get("command")
        if isinstance(value, str):
            return value

    value = payload.get("command")
    return value if isinstance(value, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    candidates: list[Any] = [
        payload.get("project_path"),
        payload.get("cwd"),
        tool_input.get("project_path") if isinstance(tool_input, dict) else None,
        tool_input.get("cwd") if isinstance(tool_input, dict) else None,
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.environ.get("PWD"),
        os.getcwd(),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return os.getcwd()


def _tokenize(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def _has_rm_rf(command: str, tokens: list[str]) -> bool:
    if RM_RF_RE.search(command):
        return True

    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        for option in tokens[index + 1 :]:
            if not option.startswith("-"):
                break
            flags = option.lstrip("-")
            if "r" in flags and "f" in flags:
                return True
    return False


def _has_force_push(tokens: list[str]) -> bool:
    for index in range(len(tokens) - 2):
        if tokens[index : index + 2] != ["git", "push"]:
            continue
        push_args = tokens[index + 2 :]
        if "--force" in push_args or "-f" in push_args:
            return True
    return False


def _has_delete_without_where(command: str) -> bool:
    for match in DELETE_FROM_RE.finditer(command):
        if not re.search(r"\bwhere\b", match.group("body"), re.IGNORECASE):
            return True
    return False


def find_block_reason(command: str) -> Optional[str]:
    tokens = _tokenize(command)

    if _has_rm_rf(command, tokens):
        return "blocks rm -rf style recursive forced deletion"
    if DROP_TABLE_RE.search(command):
        return "blocks DROP TABLE statements"
    if _has_force_push(tokens):
        return "blocks git push --force"
    if TRUNCATE_RE.search(command):
        return "blocks TRUNCATE statements"
    if _has_delete_without_where(command):
        return "blocks DELETE FROM statements without a WHERE clause"
    return None


def _log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    hooks_dir = Path(os.environ.get("CLAUDE_HOOKS_DIR", Path.home() / ".claude" / "hooks"))
    hooks_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "command": command,
        "project_path": _project_path(payload),
        "reason": reason,
    }
    with (hooks_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = _read_payload()
    tool_name = payload.get("tool_name")
    if isinstance(tool_name, str) and tool_name.lower() != "bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    _log_block(payload, command, reason)
    print(
        f"Blocked destructive Bash command: {reason}. "
        "Revise the command or ask the user for explicit confirmation before proceeding.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
