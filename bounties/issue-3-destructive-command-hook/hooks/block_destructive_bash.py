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
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class BlockReason:
    rule: str
    message: str


def normalize_sql(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip()).upper()


def has_rm_rf(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        for next_token in tokens[index + 1 :]:
            if next_token == "--":
                break
            flag = next_token.lower()
            if flag.startswith("-") and "r" in flag and "f" in flag:
                return True

    return False


def has_force_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "git":
            continue

        following = tokens[index + 1 :]
        if not following or following[0] != "push":
            continue

        if any(item in {"--force", "-f", "--force-with-lease"} for item in following[1:]):
            return True

    return False


def delete_from_without_where(sql: str) -> bool:
    for match in re.finditer(r"\bDELETE\s+FROM\b", sql):
        statement_tail = sql[match.end() :]
        statement = statement_tail.split(";", 1)[0]
        if not re.search(r"\bWHERE\b", statement):
            return True

    return False


def blocked_reason(command: str) -> BlockReason | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    sql = normalize_sql(command)

    if has_rm_rf(tokens):
        return BlockReason("rm -rf", "Recursive forced removal is blocked.")

    if has_force_push(tokens):
        return BlockReason("git push --force", "Force-pushing is blocked.")

    if re.search(r"\bDROP\s+TABLE\b", sql):
        return BlockReason("DROP TABLE", "Dropping database tables is blocked.")

    if re.search(r"\bTRUNCATE\b", sql):
        return BlockReason("TRUNCATE", "Truncating database tables is blocked.")

    if delete_from_without_where(sql):
        return BlockReason(
            "DELETE FROM without WHERE",
            "DELETE FROM statements must include a WHERE clause.",
        )

    return None


def extract_command(payload: dict[str, Any]) -> str:
    if payload.get("tool_name") != "Bash":
        return ""

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def log_block(command: str, cwd: str, reason: BlockReason) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_cwd = cwd.replace("\n", "\\n")
    LOG_PATH.open("a", encoding="utf-8").write(
        f"{timestamp}\t{reason.rule}\t{safe_cwd}\t{safe_command}\n"
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else os.getcwd()
    log_block(command, cwd, reason)
    print(
        (
            f"Blocked destructive Bash command: {reason.message} "
            f"Rule: {reason.rule}. Rewrite the command into a safer, explicit operation."
        ),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
