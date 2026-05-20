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


DENY_EVENT = "PreToolUse"
LOG_ENV_VAR = "CLAUDE_BLOCKED_LOG"


def _split_shell(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _has_rm_rf(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        flags = ""
        for next_token in tokens[index + 1 :]:
            if next_token == "--":
                break
            if not next_token.startswith("-") or next_token in {"-", "||", "&&", ";", "|"}:
                break
            flags += next_token.lstrip("-")

        if "r" in flags.lower() and "f" in flags.lower():
            return True

    return False


def _has_git_push_force(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "git":
            continue

        remainder = tokens[index + 1 :]
        if not remainder or remainder[0] != "push":
            continue

        if any(flag == "-f" or flag.startswith("--force") for flag in remainder[1:]):
            return True

    return False


def _nested_shell_commands(tokens: list[str]) -> list[str]:
    nested: list[str] = []
    for index, token in enumerate(tokens):
        if token not in {"bash", "sh", "zsh"}:
            continue
        if index + 2 < len(tokens) and tokens[index + 1] in {"-c", "-lc"}:
            nested.append(tokens[index + 2])
    return nested


def _has_drop_table(command: str) -> bool:
    return bool(re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE))


def _has_truncate_statement(command: str) -> bool:
    return bool(
        re.search(
            r"\btruncate\s+(?:table\s+)?[a-zA-Z_][\w.]*",
            command,
            flags=re.IGNORECASE,
        )
    )


def _has_delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        statement = command[match.start() :].split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def classify_command(command: str) -> str | None:
    try:
        tokens = _split_shell(command)
    except ValueError:
        tokens = []

    if _has_rm_rf(tokens):
        return "recursive forced deletion with rm -rf"
    if _has_git_push_force(tokens):
        return "force-pushing with git push --force"

    for nested in _nested_shell_commands(tokens):
        nested_reason = classify_command(nested)
        if nested_reason:
            return nested_reason

    if _has_drop_table(command):
        return "DROP TABLE statement"
    if _has_truncate_statement(command):
        return "TRUNCATE statement"
    if _has_delete_without_where(command):
        return "DELETE FROM statement without a WHERE clause"

    return None


def _read_input() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as error:
        return {"_parse_error": str(error)}


def _log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    log_path = Path(os.environ.get(LOG_ENV_VAR, "~/.claude/hooks/blocked.log")).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    project_path = (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": str(project_path),
        "command": command,
        "reason": reason,
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _deny(command: str, reason: str) -> None:
    message = (
        f"Blocked destructive Bash command: {reason}. "
        "Rewrite the command to use a safer, reversible operation or ask the user for explicit guidance."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": DENY_EVENT,
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    print(json.dumps(output))


def main() -> int:
    payload = _read_input()
    command = str(payload.get("tool_input", {}).get("command", ""))

    if payload.get("tool_name") not in {None, "Bash"}:
        return 0

    reason = classify_command(command)
    if not reason:
        return 0

    _log_block(payload, command, reason)
    _deny(command, reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
