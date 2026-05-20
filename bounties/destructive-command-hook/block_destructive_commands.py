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
from typing import Iterable


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
HARMLESS_SQL_TEXT_TOOLS = {
    "cat",
    "echo",
    "grep",
    "head",
    "less",
    "more",
    "printf",
    "rg",
    "sed",
    "tail",
}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_violation(command)
    if reason is None:
        return 0

    project_path = payload.get("cwd") or os.getcwd()
    log_blocked_attempt(command, project_path, reason)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked destructive Bash command: {reason}. "
                        "Review the command and ask the user before trying a safer alternative."
                    ),
                }
            },
            separators=(",", ":"),
        )
    )
    return 0


def find_violation(command: str) -> str | None:
    for segment in split_shell_segments(command):
        tokens = safe_split(segment)
        if not tokens:
            continue

        normalized = strip_wrappers(tokens)
        if blocks_forced_recursive_rm(normalized):
            return "recursive forced removal with rm"

        if blocks_force_push(normalized):
            return "forced git push"

        if blocks_destructive_sql(segment, normalized):
            return "destructive SQL statement"

    return None


def split_shell_segments(command: str) -> Iterable[str]:
    """Split on shell separators outside quotes so pipelines are checked piece by piece."""
    segments: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False

    for char in command:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\":
            current.append(char)
            escaped = True
            continue

        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            current.append(char)
            quote = char
            continue

        if char in {";", "\n", "|", "&"}:
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
            continue

        current.append(char)

    segment = "".join(current).strip()
    if segment:
        segments.append(segment)
    return segments


def safe_split(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def strip_wrappers(tokens: list[str]) -> list[str]:
    result = tokens[:]
    while result:
        cmd = basename(result[0])
        if cmd in {"command", "builtin", "nohup", "time"}:
            result = result[1:]
            continue

        if cmd == "sudo":
            result = result[1:]
            while result and result[0].startswith("-"):
                result = result[1:]
            continue

        if cmd == "env":
            result = result[1:]
            while result and ("=" in result[0] or result[0].startswith("-")):
                result = result[1:]
            continue

        break

    return result


def basename(token: str) -> str:
    return Path(token).name


def blocks_forced_recursive_rm(tokens: list[str]) -> bool:
    if not tokens or basename(tokens[0]) != "rm":
        return False

    recursive = False
    force = False
    for token in tokens[1:]:
        if token == "--":
            break
        if token in {"-r", "-R", "--recursive"}:
            recursive = True
        elif token in {"-f", "--force"}:
            force = True
        elif token.startswith("-") and not token.startswith("--"):
            recursive = recursive or "r" in token.lower()
            force = force or "f" in token.lower()

    return recursive and force


def blocks_force_push(tokens: list[str]) -> bool:
    if len(tokens) < 3 or basename(tokens[0]) != "git" or tokens[1] != "push":
        return False

    force_flags = {"-f", "--force", "--force-with-lease", "--force-if-includes"}
    return any(token in force_flags or token.startswith("--force=") for token in tokens[2:])


def blocks_destructive_sql(segment: str, tokens: list[str]) -> bool:
    if not tokens:
        return False

    # Allow harmless text inspection commands such as grep "DROP TABLE" migrations.sql.
    if basename(tokens[0]) in HARMLESS_SQL_TEXT_TOOLS:
        return False

    sql = segment
    if re.search(r"\bdrop\s+table\b", sql, flags=re.IGNORECASE):
        return True
    if re.search(r"\btruncate\b", sql, flags=re.IGNORECASE):
        return True

    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        statement_end = sql.find(";", match.end())
        statement = sql[match.end() : statement_end if statement_end != -1 else len(sql)]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True

    return False


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "reason": reason,
        "attempted_command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
