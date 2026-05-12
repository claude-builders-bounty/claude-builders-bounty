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


BLOCK_RULES = (
    "rm -rf or equivalent recursive forced deletion",
    "DROP TABLE statement",
    "git push --force or --force-with-lease",
    "TRUNCATE statement",
    "DELETE FROM statement without a WHERE clause",
)


def _split_shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _has_recursive_force_rm(words: Iterable[str]) -> bool:
    tokens = list(words)
    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        flags = ""
        next_index = index + 1
        while next_index < len(tokens) and tokens[next_index].startswith("-"):
            flags += tokens[next_index].lstrip("-")
            next_index += 1

        if "r" in flags and "f" in flags:
            return True

    return False


def _contains_git_force_push(command: str) -> bool:
    words = _split_shell_words(command)
    if len(words) < 3:
        return False

    for index in range(len(words) - 2):
        if words[index : index + 2] != ["git", "push"]:
            continue

        push_args = words[index + 2 :]
        return any(
            arg == "--force"
            or arg.startswith("--force=")
            or arg == "-f"
            or arg == "--force-with-lease"
            or arg.startswith("--force-with-lease=")
            for arg in push_args
        )

    return False


def _strip_sql_comments(sql: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n\r]*", " ", without_block_comments)


def _delete_without_where(sql: str) -> bool:
    cleaned = _strip_sql_comments(sql)
    for match in re.finditer(
        r"\bDELETE\s+FROM\b(?P<body>.*?)(?:;|$)",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        if not re.search(r"\bWHERE\b", match.group("body"), flags=re.IGNORECASE):
            return True
    return False


def detect_block_reasons(command: str) -> list[str]:
    reasons: list[str] = []
    words = _split_shell_words(command)

    if _has_recursive_force_rm(words):
        reasons.append(BLOCK_RULES[0])

    if re.search(r"\bDROP\s+TABLE\b", command, flags=re.IGNORECASE):
        reasons.append(BLOCK_RULES[1])

    if _contains_git_force_push(command):
        reasons.append(BLOCK_RULES[2])

    if re.search(r"\bTRUNCATE\b", command, flags=re.IGNORECASE):
        reasons.append(BLOCK_RULES[3])

    if _delete_without_where(command):
        reasons.append(BLOCK_RULES[4])

    return reasons


def log_blocked_attempt(command: str, project_path: str) -> Path:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return log_path


def build_block_message(reasons: Iterable[str], log_path: Path) -> str:
    reason_text = "; ".join(reasons)
    return (
        "Blocked destructive Bash command before execution. "
        f"Reason: {reason_text}. "
        f"The attempt was logged to {log_path}. "
        "Use a narrower, reversible command or ask the user for an explicit safe alternative."
    )


def build_pre_tool_use_deny_output(reasons: Iterable[str], log_path: Path) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": build_block_message(reasons, log_path),
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid Claude hook JSON input: {exc}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reasons = detect_block_reasons(command)
    if not reasons:
        return 0

    project_path = (
        os.environ.get("CLAUDE_PROJECT_DIR")
        or str(payload.get("cwd") or "")
        or os.getcwd()
    )
    log_path = log_blocked_attempt(command, project_path)
    print(json.dumps(build_pre_tool_use_deny_output(reasons, log_path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
