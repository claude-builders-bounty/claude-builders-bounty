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


BLOCK_EXIT_CODE = 2


def main() -> int:
    payload = read_payload()
    if not is_bash_tool(payload):
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = destructive_reason(command)
    if reason is None:
        return 0

    project_path = extract_project_path(payload)
    log_blocked_attempt(command, project_path, reason)
    print(
        f"Blocked destructive Bash command: {reason}. "
        "The command was not executed.",
        file=sys.stderr,
    )
    return BLOCK_EXIT_CODE


def read_payload() -> dict[str, Any]:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return {}
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        return {}

    return payload if isinstance(payload, dict) else {}


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name") or payload.get("tool")
    if isinstance(tool_name, dict):
        tool_name = tool_name.get("name")

    return isinstance(tool_name, str) and tool_name.lower() == "bash"


def extract_command(payload: dict[str, Any]) -> str | None:
    candidate_paths = (
        ("tool_input", "command"),
        ("input", "command"),
        ("command",),
    )

    for path in candidate_paths:
        value: Any = payload
        for key in path:
            if not isinstance(value, dict) or key not in value:
                value = None
                break
            value = value[key]

        if isinstance(value, str) and value.strip():
            return value

    return None


def extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        cwd = tool_input.get("cwd")
        if isinstance(cwd, str) and cwd.strip():
            return cwd

    return os.getcwd()


def destructive_reason(command: str) -> str | None:
    checks = (
        (contains_rm_rf, "rm -rf removes files recursively and forcibly"),
        (contains_force_push, "git push --force rewrites remote history"),
        (contains_drop_table, "DROP TABLE removes an entire database table"),
        (contains_truncate, "TRUNCATE removes all rows from a table"),
        (
            contains_delete_without_where,
            "DELETE FROM without WHERE can remove all rows from a table",
        ),
    )

    for check, reason in checks:
        if check(command):
            return reason

    return None


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return []


def contains_rm_rf(command: str) -> bool:
    tokens = shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "rm" and not token.endswith("/rm"):
            continue

        option_tokens = []
        for next_token in tokens[index + 1 :]:
            if next_token == "--":
                break
            if not next_token.startswith("-"):
                break
            option_tokens.append(next_token)

        short_flags = "".join(
            token[1:] for token in option_tokens if token.startswith("-") and not token.startswith("--")
        ).lower()
        has_recursive = "r" in short_flags or any(
            token in ("--recursive", "-R") for token in option_tokens
        )
        has_force = "f" in short_flags or "--force" in option_tokens
        if has_recursive and has_force:
            return True

    return bool(re.search(r"(^|[;&|]\s*)rm\s+-[A-Za-z]*r[A-Za-z]*f", command))


def contains_force_push(command: str) -> bool:
    tokens = shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "git" and not token.endswith("/git"):
            continue

        tail = tokens[index + 1 :]
        if "push" not in tail:
            continue

        push_index = tail.index("push")
        push_args = tail[push_index + 1 :]
        if any(arg in ("--force", "--force-with-lease", "-f") for arg in push_args):
            return True
        if any(arg.startswith("--force=") or arg.startswith("--force-with-lease=") for arg in push_args):
            return True

    return False


def contains_drop_table(command: str) -> bool:
    return bool(re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE))


def contains_truncate(command: str) -> bool:
    return bool(re.search(r"\btruncate(?:\s+table)?\b", command, flags=re.IGNORECASE))


def contains_delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        remainder = command[match.end() :]
        statement = remainder.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True

    return False


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    hooks_dir = os.environ.get("CLAUDE_HOOKS_DIR")
    log_dir = Path(hooks_dir) if hooks_dir else Path.home() / ".claude" / "hooks"
    log_path = log_dir / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
