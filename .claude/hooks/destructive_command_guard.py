#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Install this file at ~/.claude/hooks/destructive_command_guard.py and configure it
as a PreToolUse hook for the Bash tool. The hook reads Claude Code's JSON hook
payload from stdin and exits with code 2 when a command should be blocked.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


SQL_DELETE_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE | re.DOTALL)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)
DROP_TABLE_RE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE | re.DOTALL)
TRUNCATE_RE = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)
SQL_CLIENTS = {
    "mysql",
    "mariadb",
    "psql",
    "sqlite3",
    "sqlcmd",
}


def _load_payload() -> dict[str, Any]:
    """Return the hook JSON payload, or an empty dict for malformed/empty input."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command

    # Be permissive for local testing or future payload variants.
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    candidates: list[Any] = [
        payload.get("cwd"),
        payload.get("project_path"),
        payload.get("project_dir"),
        payload.get("workspace"),
    ]
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        candidates.extend(
            [
                tool_input.get("cwd"),
                tool_input.get("project_path"),
                tool_input.get("working_directory"),
            ]
        )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return os.environ.get("PWD", os.getcwd())


def _shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # Fall back to a conservative whitespace split for incomplete quoting.
        return command.split()


def _contains_rm_rf(command: str) -> bool:
    """Detect rm invocations whose options include both recursive and force."""
    separators = {";", "&&", "||", "|", "&"}
    words = _shell_words(command)
    for index, word in enumerate(words):
        base = os.path.basename(word)
        if base != "rm":
            continue

        has_recursive = False
        has_force = False
        for option in words[index + 1 :]:
            if option in separators:
                break
            if option == "--":
                break
            if option.startswith("--"):
                if option in {"--recursive", "--dir"}:
                    has_recursive = True
                if option == "--force":
                    has_force = True
                continue
            if option.startswith("-") and len(option) > 1:
                flags = option[1:]
                if "r" in flags or "R" in flags:
                    has_recursive = True
                if "f" in flags:
                    has_force = True
                continue
            # rm operands start; no more options for this rm invocation.
            break
        if has_recursive and has_force:
            return True
    return False


def _contains_sql_client(command: str) -> bool:
    """Return whether command invokes a known SQL client.

    The SQL phrase checks are intentionally scoped to SQL clients so harmless
    text operations such as echo/grep/cat heredocs containing SQL examples do
    not get blocked.
    """
    return any(os.path.basename(word) in SQL_CLIENTS for word in _shell_words(command))


def _contains_delete_without_where(command: str) -> bool:
    """Detect DELETE FROM statements that do not include WHERE before statement end."""
    for match in SQL_DELETE_RE.finditer(command):
        statement_tail = command[match.end() :]
        statement_tail = re.split(r"[;\n]", statement_tail, maxsplit=1)[0]
        if not WHERE_RE.search(statement_tail):
            return True
    return False


def _contains_git_force_push(command: str) -> bool:
    """Detect git push invocations that use force-push flags.

    Handles git global options before the subcommand, for example
    ``git -C repo push --force``, and wrappers such as ``sudo -n git ...`` by
    scanning for every git token in the shell words.
    """
    words = _shell_words(command)
    separators = {";", "&&", "||", "|", "&"}

    index = 0
    while index < len(words):
        if os.path.basename(words[index]) != "git":
            index += 1
            continue

        cursor = index + 1
        while cursor < len(words):
            word = words[cursor]
            if word in separators:
                break
            if word == "push":
                for option in words[cursor + 1 :]:
                    if option in separators:
                        break
                    if option == "--":
                        continue
                    if option == "-f" or option.startswith("--force"):
                        return True
                break
            if word in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
                cursor += 2
                continue
            if word.startswith(("-C", "-c")) and word not in {"-C", "-c"}:
                cursor += 1
                continue
            if word.startswith(("--git-dir=", "--work-tree=", "--namespace=")):
                cursor += 1
                continue
            if word.startswith("-"):
                cursor += 1
                continue
            break

        index += 1
    return False


def blocked_reason(command: str) -> str | None:
    """Return a human-readable reason if command is destructive, else None."""
    checks = [
        (_contains_rm_rf, "recursive forced deletion with rm -rf"),
        (
            lambda c: _contains_sql_client(c) and bool(DROP_TABLE_RE.search(c)),
            "SQL DROP TABLE statement",
        ),
        (
            lambda c: _contains_sql_client(c) and bool(TRUNCATE_RE.search(c)),
            "SQL TRUNCATE statement",
        ),
        (_contains_git_force_push, "force push with git push --force"),
        (
            lambda c: _contains_sql_client(c) and _contains_delete_without_where(c),
            "DELETE FROM statement without a WHERE clause",
        ),
    ]
    for check, reason in checks:
        if check(command):
            return reason
    return None


def _log_block(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = _load_payload()

    # This hook is intended for Bash PreToolUse events. If it is accidentally
    # configured more broadly, do not interfere with non-Bash tools.
    tool_name = payload.get("tool_name")
    if isinstance(tool_name, str) and tool_name.lower() != "bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_block(command, project_path, reason)
    print(
        "Blocked destructive Bash command: "
        f"{reason}. The command was not executed and was logged to {LOG_PATH}.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
