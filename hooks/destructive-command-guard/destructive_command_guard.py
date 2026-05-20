#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _normalize_sql(text: str) -> str:
    without_line_comments = re.sub(r"--.*?$", " ", text, flags=re.MULTILINE)
    without_block_comments = re.sub(r"/\*.*?\*/", " ", without_line_comments, flags=re.DOTALL)
    return re.sub(r"\s+", " ", without_block_comments).strip().upper()


def _split_shell(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _has_rm_rf(tokens: Iterable[str]) -> bool:
    tokens = list(tokens)
    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        recursive = False
        force = False
        for option in tokens[index + 1 :]:
            if not option.startswith("-"):
                break
            if option == "--":
                break
            if option in {"-r", "-R", "--recursive", "-d"}:
                recursive = True
            if option in {"-f", "--force"}:
                force = True
            if option.startswith("-") and not option.startswith("--"):
                recursive = recursive or "r" in option.lower()
                force = force or "f" in option.lower()
        if recursive and force:
            return True
    return False


def _has_force_push(tokens: Iterable[str]) -> bool:
    tokens = list(tokens)
    for index in range(len(tokens) - 2):
        if tokens[index : index + 2] != ["git", "push"]:
            continue
        push_args = tokens[index + 2 :]
        if any(arg in {"-f", "--force", "--force-with-lease"} for arg in push_args):
            return True
        if any(arg.startswith("--force=") or arg.startswith("--force-with-lease=") for arg in push_args):
            return True
    return False


def _has_destructive_sql(command: str) -> tuple[bool, str]:
    sql = _normalize_sql(command)
    if re.search(r"\bDROP\s+TABLE\b", sql):
        return True, "DROP TABLE statement"
    if re.search(r"\bTRUNCATE\b", sql):
        return True, "TRUNCATE statement"

    for match in re.finditer(r"\bDELETE\s+FROM\b", sql):
        statement = sql[match.start() :]
        statement = statement.split(";", 1)[0]
        if not re.search(r"\bWHERE\b", statement):
            return True, "DELETE FROM statement without WHERE"

    return False, ""


def classify_command(command: str) -> str | None:
    tokens = _split_shell(command)
    if _has_rm_rf(tokens):
        return "recursive forced removal"
    if _has_force_push(tokens):
        return "force push"

    sql_blocked, reason = _has_destructive_sql(command)
    if sql_blocked:
        return reason

    return None


def deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive command: {reason}. "
                "Use a safer command or ask the user for explicit confirmation."
            ),
        }
    }
    print(json.dumps(payload, separators=(",", ":")))


def log_block(command: str, cwd: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    row = {
        "timestamp": timestamp,
        "project_path": cwd,
        "reason": reason,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Invalid hook input JSON: {error}", file=sys.stderr)
        return 1

    if event.get("hook_event_name") != "PreToolUse" or event.get("tool_name") != "Bash":
        return 0

    command = str(event.get("tool_input", {}).get("command", ""))
    reason = classify_command(command)
    if not reason:
        return 0

    cwd = str(event.get("cwd") or os.getcwd())
    log_block(command, cwd, reason)
    print(f"Destructive command blocked: {reason}", file=sys.stderr)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

