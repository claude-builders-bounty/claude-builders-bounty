#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell/SQL commands."""

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


BLOCK_EXIT_CODE = 2
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class BlockReason:
    rule: str
    message: str


def normalize_command(command: str) -> str:
    """Collapse whitespace and strip surrounding space for safer matching."""
    return re.sub(r"\s+", " ", command).strip()


def extract_command(payload: dict[str, Any]) -> str:
    """Extract the shell command from common Claude Code hook payload shapes."""
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}

    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "bash_command", "input"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value

    for key in ("command", "cmd"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    """Find a useful project path for the audit log."""
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    candidates = [
        payload.get("cwd"),
        payload.get("project_path"),
        payload.get("projectPath"),
        os.environ.get("CLAUDE_PROJECT_DIR"),
    ]

    if isinstance(tool_input, dict):
        candidates.extend([tool_input.get("cwd"), tool_input.get("workdir")])

    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value

    return os.getcwd()


def is_bash_tool(payload: dict[str, Any]) -> bool:
    """Only enforce this hook on shell-like tool calls."""
    tool_name = payload.get("tool_name") or payload.get("toolName") or ""
    if not tool_name:
        return True
    return str(tool_name).lower() in {"bash", "shell", "terminal"}


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", " ", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return sql


def delete_from_without_where(command: str) -> bool:
    """Detect DELETE FROM statements that do not contain WHERE before statement end."""
    sql = strip_sql_comments(command)
    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        statement = sql[match.start() :]
        statement = statement.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def rm_rf_detected(command: str) -> bool:
    """Detect rm commands containing both recursive and force flags."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    for idx, token in enumerate(tokens):
        if token != "rm":
            continue

        flags = []
        for next_token in tokens[idx + 1 :]:
            if next_token == "--":
                break
            if not next_token.startswith("-"):
                continue
            flags.extend(next_token[1:])

        if "r" in flags and "f" in flags:
            return True

    return False


def git_force_push_detected(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    for i, token in enumerate(tokens):
        if token != "git":
            continue

        git_args = tokens[i + 1 :]
        if "push" not in git_args:
            continue

        push_index = git_args.index("push")
        push_args = git_args[push_index + 1 :]
        if (
            "--force" in push_args
            or "-f" in push_args
            or "--force-with-lease" in push_args
        ):
            return True
    return False


def find_block_reason(command: str) -> BlockReason | None:
    command = normalize_command(command)
    if not command:
        return None

    if rm_rf_detected(command):
        return BlockReason("rm -rf", "Recursive forced deletion is blocked.")

    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return BlockReason("DROP TABLE", "Dropping database tables is blocked.")

    if git_force_push_detected(command):
        return BlockReason("git push --force", "Force-pushing Git history is blocked.")

    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return BlockReason("TRUNCATE", "Truncating database tables is blocked.")

    if delete_from_without_where(command):
        return BlockReason(
            "DELETE FROM without WHERE",
            "DELETE FROM statements must include a WHERE clause.",
        )

    return None


def log_blocked_attempt(command: str, project_path: str, reason: BlockReason) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "project_path": project_path,
        "rule": reason.rule,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not isinstance(payload, dict) or not is_bash_tool(payload):
        return 0

    command = extract_command(payload)
    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = extract_project_path(payload)
    log_blocked_attempt(command, project_path, reason)
    print(
        f"Blocked command: {reason.message} Rule: {reason.rule}. "
        f"Attempt was logged to {LOG_PATH}.",
        file=sys.stderr,
    )
    return BLOCK_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
