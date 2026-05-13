#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads the JSON payload Claude Code sends to command hooks on stdin.
It exits with code 2 when a Bash command should be blocked, which tells
Claude Code to stop the tool call and show the message printed by this script.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


class BlockedCommand(Exception):
    """Raised when a command matches a destructive pattern."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def normalize_command(command: str) -> str:
    """Collapse whitespace and strip harmless wrapping spaces."""
    return re.sub(r"\s+", " ", command.strip())


def strip_sql_comments(sql: str) -> str:
    """Remove simple SQL comments before pattern checks."""
    without_line_comments = re.sub(r"--.*?(?=\n|$)", " ", sql)
    return re.sub(r"/\*.*?\*/", " ", without_line_comments, flags=re.DOTALL)


def shell_words(command: str) -> list[str]:
    """Best-effort shell tokenization.

    If a command has unmatched quotes, fall back to whitespace splitting so the
    hook remains conservative instead of silently allowing dangerous input.
    """
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def contains_rm_rf(command: str) -> bool:
    """Detect rm invocations with both recursive and force flags."""
    tokens = shell_words(command)
    for index, token in enumerate(tokens):
        if token.endswith("rm") or token == "rm":
            flags = ""
            for next_token in tokens[index + 1 :]:
                if next_token == "--":
                    break
                if not next_token.startswith("-"):
                    continue
                flags += next_token.lstrip("-")
            if "r" in flags and "f" in flags:
                return True
    return False


def contains_force_push(command: str) -> bool:
    """Detect git push commands that use force flags."""
    tokens = shell_words(command)
    for index in range(len(tokens) - 2):
        if tokens[index] == "git" and tokens[index + 1] == "push":
            push_args = tokens[index + 2 :]
            return any(arg == "--force" or arg.startswith("--force=") for arg in push_args)
    return False


def contains_delete_without_where(command: str) -> bool:
    """Detect DELETE FROM statements with no WHERE before statement end."""
    sql = strip_sql_comments(command)
    for match in re.finditer(r"\bDELETE\s+FROM\b", sql, flags=re.IGNORECASE):
        remainder = sql[match.end() :]
        statement = re.split(r";|&&|\|\||\n", remainder, maxsplit=1)[0]
        if not re.search(r"\bWHERE\b", statement, flags=re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    """Return the first destructive-command reason, or None when safe."""
    normalized = normalize_command(command)
    if not normalized:
        return None

    if contains_rm_rf(normalized):
        return "recursive force deletion (`rm -rf`) can permanently remove files"
    if re.search(r"\bDROP\s+TABLE\b", normalized, flags=re.IGNORECASE):
        return "`DROP TABLE` can permanently remove database schema and data"
    if contains_force_push(normalized):
        return "`git push --force` can overwrite remote history"
    if re.search(r"\bTRUNCATE\b", normalized, flags=re.IGNORECASE):
        return "`TRUNCATE` can permanently delete table contents"
    if contains_delete_without_where(normalized):
        return "`DELETE FROM` without a `WHERE` clause can delete every row"
    return None


def extract_command(payload: dict[str, Any]) -> str:
    """Extract Bash command from known Claude Code hook payload shapes."""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd")
        if isinstance(command, str):
            return command
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def project_path(payload: dict[str, Any]) -> str:
    """Get project path from env or payload for logging."""
    for key in ("CLAUDE_PROJECT_DIR", "PWD"):
        value = os.environ.get(key)
        if value:
            return value
    for key in ("project_path", "project_dir", "cwd"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "unknown"


def write_block_log(command: str, project: str, reason: str) -> None:
    """Append a blocked attempt to ~/.claude/hooks/blocked.log."""
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project,
        "reason": reason,
        "command": command,
    }
    with BLOCK_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    """Hook entrypoint."""
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {"command": raw}

    command = extract_command(payload)
    reason = block_reason(command)
    if not reason:
        return 0

    project = project_path(payload)
    write_block_log(command, project, reason)
    print(
        "Blocked destructive Bash command before execution.\n"
        f"Reason: {reason}.\n"
        f"Project: {project}\n"
        "Choose a safer command, add an explicit WHERE clause, or ask the user "
        "for confirmation before attempting destructive operations.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
