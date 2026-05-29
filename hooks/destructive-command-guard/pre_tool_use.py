#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
SQL_DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
SQL_TRUNCATE = re.compile(r"\btruncate\b", re.IGNORECASE)
SQL_DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)


@dataclass(frozen=True)
class BlockDecision:
    rule: str
    reason: str


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def split_subcommands(tokens: Iterable[str]) -> list[list[str]]:
    subcommands: list[list[str]] = []
    current: list[str] = []
    separators = {";", "&&", "||", "|", "\n", "(", ")"}

    for token in tokens:
        if token in separators or set(token) <= {";", "&", "|", "(", ")"}:
            if current:
                subcommands.append(current)
                current = []
            continue
        current.append(token)

    if current:
        subcommands.append(current)

    return subcommands


def strip_wrappers(tokens: list[str]) -> list[str]:
    stripped = list(tokens)

    while stripped and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", stripped[0]):
        stripped.pop(0)

    while stripped and stripped[0] in {"sudo", "command"}:
        stripped.pop(0)

    if stripped and stripped[0] == "env":
        stripped.pop(0)
        while stripped and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", stripped[0]):
            stripped.pop(0)

    return stripped


def command_name(token: str) -> str:
    return token.replace("\\", "/").rsplit("/", 1)[-1]


def has_rm_recursive_force(tokens: list[str]) -> bool:
    stripped = strip_wrappers(tokens)
    if not stripped or command_name(stripped[0]) != "rm":
        return False

    recursive = False
    force = False
    for token in stripped[1:]:
        if not token.startswith("-") or token == "--":
            continue
        option_chars = token.lstrip("-")
        recursive = recursive or "r" in option_chars or "R" in option_chars
        force = force or "f" in option_chars

    return recursive and force


def has_force_push(tokens: list[str]) -> bool:
    stripped = strip_wrappers(tokens)
    if not stripped or command_name(stripped[0]) != "git":
        return False

    has_push = any(token == "push" for token in stripped[1:])
    has_force = any(
        token in {"-f", "--force", "--force-with-lease"} or token.startswith("--force=")
        for token in stripped[1:]
    )
    return has_push and has_force


def delete_without_where(command: str) -> bool:
    for match in SQL_DELETE_FROM.finditer(command):
        statement_tail = command[match.end() :]
        statement = statement_tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def detect_block(command: str) -> BlockDecision | None:
    tokens = tokenize(command)
    for subcommand in split_subcommands(tokens):
        if has_rm_recursive_force(subcommand):
            return BlockDecision(
                "rm-rf",
                "Blocked recursive forced deletion. Remove files more narrowly or ask for explicit human confirmation.",
            )
        if has_force_push(subcommand):
            return BlockDecision(
                "git-force-push",
                "Blocked force push because it can rewrite shared history.",
            )

    if SQL_DROP_TABLE.search(command):
        return BlockDecision(
            "drop-table",
            "Blocked DROP TABLE because it can destroy schema and data.",
        )

    if SQL_TRUNCATE.search(command):
        return BlockDecision(
            "truncate",
            "Blocked TRUNCATE because it can remove all rows from a table.",
        )

    if delete_without_where(command):
        return BlockDecision(
            "delete-without-where",
            "Blocked DELETE FROM without a WHERE clause.",
        )

    return None


def project_path(payload: dict) -> str:
    return (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def log_block(command: str, decision: BlockDecision, cwd: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": cwd,
        "rule": decision.rule,
        "reason": decision.reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def deny_output(decision: BlockDecision) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": decision.reason,
        },
        "systemMessage": decision.reason,
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    decision = detect_block(command)
    if decision is None:
        return 0

    cwd = project_path(payload)
    log_block(command, decision, cwd)
    print(json.dumps(deny_output(decision)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
