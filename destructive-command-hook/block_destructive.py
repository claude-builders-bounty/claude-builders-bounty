#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_MESSAGE = (
    "Blocked destructive Bash command: matched {rule}. Remove the destructive "
    "operation or ask the user for an explicit safer plan."
)


TEXT_ONLY_COMMANDS = {"echo", "printf"}


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def command_segments(command: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    quote: str | None = None
    index = 0

    while index < len(command):
        char = command[index]

        if quote:
            current.append(char)
            if char == quote:
                quote = None
            index += 1
            continue

        if char in ("'", '"'):
            quote = char
            current.append(char)
            index += 1
            continue

        if char in (";", "\n") or command[index : index + 2] in ("&&", "||"):
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
            index += 2 if command[index : index + 2] in ("&&", "||") else 1
            continue

        current.append(char)
        index += 1

    segment = "".join(current).strip()
    if segment:
        segments.append(segment)

    return segments


def compact_sql(command: str) -> str:
    """Return SQL-ish text with normalized whitespace for pattern checks."""
    return re.sub(r"\s+", " ", command).strip()


def has_unsafe_delete(command: str) -> bool:
    sql = compact_sql(command)
    for match in re.finditer(r"\bDELETE\s+FROM\b", sql, flags=re.IGNORECASE):
        tail = sql[match.end() :]
        end = re.search(r";|&&|\|\||\n", tail)
        statement_tail = tail[: end.start()] if end else tail
        if not re.search(r"\bWHERE\b", statement_tail, flags=re.IGNORECASE):
            return True
    return False


def matched_rule(command: str) -> str | None:
    for segment in command_segments(command):
        rule = matched_segment_rule(segment)
        if rule:
            return rule
    return None


def matched_segment_rule(command: str) -> str | None:
    words = shell_words(command)
    if not words:
        return None

    executable = Path(words[0]).name.lower()

    if executable == "rm":
        flags = "".join(word[1:] for word in words[1:] if word.startswith("-") and word != "--")
        if "r" in flags.lower() and "f" in flags.lower():
            return "rm -rf"

    if executable == "git" and len(words) >= 3 and words[1] == "push":
        force_flags = (
            word == "-f"
            or word == "--force"
            or word.startswith("--force=")
            or word.startswith("--force-with-lease")
            for word in words[2:]
        )
        if any(force_flags):
            return "git push --force"

    if executable not in TEXT_ONLY_COMMANDS:
        checks: list[tuple[str, re.Pattern[str]]] = [
            ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
            ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
        ]

        for name, pattern in checks:
            if pattern.search(command):
                return name

        if has_unsafe_delete(command):
            return "DELETE FROM without WHERE"

    return None


def read_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def extract_command(payload: dict[str, Any]) -> str:
    if payload.get("tool_name") != "Bash":
        return ""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def log_block(command: str, project: str, rule: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project,
        "rule": rule,
    }
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def deny(rule: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": BLOCK_MESSAGE.format(rule=rule),
                }
            }
        )
    )


def main() -> int:
    payload = read_payload()
    command = extract_command(payload)
    rule = matched_rule(command)

    if rule:
        log_block(command, project_path(payload), rule)
        deny(rule)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
