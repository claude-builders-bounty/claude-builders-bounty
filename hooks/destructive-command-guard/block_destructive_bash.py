#!/usr/bin/env python3
"""Claude Code PreToolUse hook for blocking destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_TABLE_RE = re.compile(
    r"\btruncate\s+(?:table\s+)?[a-zA-Z_\"`][\w\"`.-]*", re.IGNORECASE
)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
SHELL_SPLIT_RE = re.compile(r"(?:&&|\|\||;|\n)")


def _load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_bash_command(payload: dict[str, Any]) -> str | None:
    if payload.get("hook_event_name") != "PreToolUse":
        return None
    if payload.get("tool_name") != "Bash":
        return None

    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd")
    elif isinstance(tool_input, str):
        command = tool_input
    else:
        command = None

    return command if isinstance(command, str) and command.strip() else None


def _tokenize_shell_segment(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def _strip_command_prefixes(tokens: list[str]) -> list[str]:
    while tokens and "=" in tokens[0] and not tokens[0].startswith("-"):
        name = tokens[0].split("=", 1)[0]
        if not name or not name.replace("_", "").isalnum():
            break
        tokens = tokens[1:]

    while tokens and tokens[0] in {"sudo", "command"}:
        tokens = tokens[1:]

    return tokens


def _has_recursive_force_rm(command: str) -> bool:
    for segment in SHELL_SPLIT_RE.split(command):
        tokens = _strip_command_prefixes(_tokenize_shell_segment(segment.strip()))
        if not tokens or tokens[0] != "rm":
            continue

        short_flags = ""
        long_flags: set[str] = set()

        for arg in tokens[1:]:
            if arg == "--":
                break
            if arg.startswith("--"):
                long_flags.add(arg)
            elif arg.startswith("-") and len(arg) > 1:
                short_flags += arg[1:]

        has_recursive = "r" in short_flags or "R" in short_flags or "--recursive" in long_flags
        has_force = "f" in short_flags or "--force" in long_flags
        if has_recursive and has_force:
            return True

    return False


def _has_force_push(command: str) -> bool:
    for segment in SHELL_SPLIT_RE.split(command):
        tokens = _strip_command_prefixes(_tokenize_shell_segment(segment.strip()))
        if len(tokens) >= 3 and tokens[0] == "git" and tokens[1] == "push":
            if any(token in {"--force", "-f"} or token.startswith("--force=") for token in tokens[2:]):
                return True
    return False


def _has_delete_without_where(command: str) -> bool:
    for match in DELETE_FROM_RE.finditer(command):
        statement_tail = command[match.end() :]
        statement = statement_tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def detect_block_reasons(command: str) -> list[str]:
    reasons: list[str] = []

    if _has_recursive_force_rm(command):
        reasons.append("recursive forced deletion via rm")
    if DROP_TABLE_RE.search(command):
        reasons.append("DROP TABLE statement")
    if TRUNCATE_TABLE_RE.search(command):
        reasons.append("TRUNCATE statement")
    if _has_force_push(command):
        reasons.append("forced git push")
    if _has_delete_without_where(command):
        reasons.append("DELETE FROM without WHERE clause")

    return reasons


def _project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _log_blocked_attempt(command: str, project_path: str, reasons: list[str]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "reason": "; ".join(reasons),
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def _deny_message(command: str, project_path: str, reasons: list[str]) -> str:
    reason_text = ", ".join(reasons)
    return (
        "Blocked destructive Bash command before execution. "
        f"Reason: {reason_text}. Project: {project_path}. "
        "Choose a safer command or ask the user to approve the destructive operation explicitly. "
        f"Attempted command: {command}"
    )


def main() -> int:
    payload = _load_payload()
    command = _extract_bash_command(payload)
    if command is None:
        return 0

    reasons = detect_block_reasons(command)
    if not reasons:
        return 0

    project_path = _project_path(payload)
    _log_blocked_attempt(command, project_path, reasons)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _deny_message(command, project_path, reasons),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
