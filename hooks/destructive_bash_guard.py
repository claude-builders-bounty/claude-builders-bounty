#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads the Claude Code hook event JSON from stdin. When the event is a Bash tool
call and the command is dangerous, it logs the attempt and returns a deny
permission decision using Claude Code's hookSpecificOutput format.
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

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_SQL_RE = re.compile(
    r"\b(drop\s+table|truncate(?:\s+table)?|delete\s+from\b)",
    re.IGNORECASE | re.DOTALL,
)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def _extract_command(event: dict[str, Any]) -> str:
    """Extract Bash command text from common Claude Code hook payload shapes."""
    tool_input = event.get("tool_input") or event.get("toolInput") or event.get("input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        return str(command)
    return ""


def _tool_name(event: dict[str, Any]) -> str:
    return str(event.get("tool_name") or event.get("toolName") or event.get("tool") or "")


def _project_path(event: dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "projectDir", "workspace", "path"):
        value = event.get(key)
        if value:
            return str(value)
    tool_input = event.get("tool_input") or event.get("toolInput") or {}
    if isinstance(tool_input, dict):
        for key in ("cwd", "project_dir", "projectDir"):
            value = tool_input.get(key)
            if value:
                return str(value)
    return os.getcwd()


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # Fall back to whitespace splitting for malformed shell snippets.
        return command.split()


def _has_rm_rf(command: str) -> bool:
    tokens = _shell_tokens(command)
    # Catch common nested shell forms such as: bash -c 'rm -rf dist'
    for i, token in enumerate(tokens[:-1]):
        if token in {"bash", "sh", "/bin/bash", "/bin/sh"} and "-c" in tokens[i + 1 : i + 3]:
            c_index = tokens.index("-c", i + 1)
            if c_index + 1 < len(tokens) and _has_rm_rf(tokens[c_index + 1]):
                return True
        if token == "eval" and i + 1 < len(tokens) and _has_rm_rf(" ".join(tokens[i + 1 :])):
            return True
    for i, token in enumerate(tokens):
        if token in {"rm", "/bin/rm", "rm.exe"} or token.endswith("/rm"):
            j = i + 1
            while j < len(tokens):
                arg = tokens[j]
                if arg == "--":
                    break
                if arg.startswith("-") and "r" in arg.lower() and "f" in arg.lower():
                    return True
                # Support separated flags: rm -r -f target / rm -f -R target
                if arg.startswith("-") and "r" in arg.lower():
                    if any(t.startswith("-") and "f" in t.lower() for t in tokens[j + 1 : j + 3]):
                        return True
                if arg.startswith("-") and "f" in arg.lower():
                    if any(t.startswith("-") and "r" in t.lower() for t in tokens[j + 1 : j + 3]):
                        return True
                if not arg.startswith("-"):
                    break
                j += 1
    return False


def _has_git_push_force(command: str) -> bool:
    tokens = _shell_tokens(command)
    for i, token in enumerate(tokens[:-1]):
        if token in {"bash", "sh", "/bin/bash", "/bin/sh"} and "-c" in tokens[i + 1 : i + 3]:
            c_index = tokens.index("-c", i + 1)
            if c_index + 1 < len(tokens) and _has_git_push_force(tokens[c_index + 1]):
                return True
        if token == "eval" and i + 1 < len(tokens) and _has_git_push_force(" ".join(tokens[i + 1 :])):
            return True
    for i in range(len(tokens) - 2):
        if tokens[i] == "git" and tokens[i + 1] == "push":
            push_args = tokens[i + 2 :]
            for arg in push_args:
                if arg == "--":
                    break
                if arg in {"--force", "-f", "--force-with-lease", "--force-if-includes"}:
                    return True
                if arg.startswith("--force=") or arg.startswith("--force-with-lease="):
                    return True
    return False


def _sql_payloads(command: str) -> list[str]:
    """Return strings that are likely executed as SQL, not docs/search text."""
    tokens = _shell_tokens(command)
    payloads: list[str] = []

    for i, token in enumerate(tokens):
        exe = Path(token).name.lower()
        if exe in {"psql", "mysql", "mariadb", "sqlite3", "duckdb"}:
            j = i + 1
            while j < len(tokens):
                arg = tokens[j]
                if arg in {"-c", "-e", "--execute", "--command"} and j + 1 < len(tokens):
                    payloads.append(tokens[j + 1])
                    j += 2
                    continue
                if arg.startswith("--execute=") or arg.startswith("--command="):
                    payloads.append(arg.split("=", 1)[1])
                # sqlite3/duckdb commonly accept SQL as a positional argument after the DB path.
                if exe in {"sqlite3", "duckdb"} and j > i + 1 and not arg.startswith("-"):
                    payloads.append(arg)
                j += 1

    # Catch nested shell forms such as: bash -c "psql -c 'DROP TABLE users'"
    for i, token in enumerate(tokens[:-1]):
        if token in {"bash", "sh", "/bin/bash", "/bin/sh"} and "-c" in tokens[i + 1 : i + 3]:
            c_index = tokens.index("-c", i + 1)
            if c_index + 1 < len(tokens):
                payloads.extend(_sql_payloads(tokens[c_index + 1]))
        if token == "eval" and i + 1 < len(tokens):
            payloads.extend(_sql_payloads(" ".join(tokens[i + 1 :])))

    return payloads


def _sql_reason(command: str) -> str | None:
    payloads = _sql_payloads(command)
    if not payloads:
        return None

    for sql in payloads:
        reason = _sql_payload_reason(sql)
        if reason:
            return reason
    return None


def _sql_payload_reason(sql: str) -> str | None:
    for match in DANGEROUS_SQL_RE.finditer(sql):
        keyword = re.sub(r"\s+", " ", match.group(1).upper())
        if keyword.startswith("DELETE FROM"):
            # Evaluate the statement after DELETE FROM until a statement separator.
            tail = sql[match.end() :]
            statement_tail = re.split(r";", tail, maxsplit=1)[0]
            if WHERE_RE.search(statement_tail):
                continue
            return "DELETE FROM without a WHERE clause can wipe an entire table."
        if keyword.startswith("DROP TABLE"):
            return "DROP TABLE can permanently remove database tables."
        if keyword.startswith("TRUNCATE"):
            return "TRUNCATE can permanently remove all rows from a table."
        return f"Dangerous SQL statement detected: {keyword}."
    return None


def dangerous_reason(command: str) -> str | None:
    if not command.strip():
        return None
    if _has_rm_rf(command):
        return "rm -rf recursively and forcibly deletes files."
    if _has_git_push_force(command):
        return "git push --force can overwrite shared remote history."
    sql_reason = _sql_reason(command)
    if sql_reason:
        return sql_reason
    return None


def _log_block(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _allow() -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
        }
    }


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: " + reason +
                " Use a safer, reversible command or ask the user for explicit approval."
            ),
        }
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps(_deny(f"invalid hook JSON: {exc}")))
        return 0

    if _tool_name(event) != "Bash":
        print(json.dumps(_allow()))
        return 0

    command = _extract_command(event)
    reason = dangerous_reason(command)
    if reason:
        project_path = _project_path(event)
        _log_block(command, project_path, reason)
        print(json.dumps(_deny(reason)))
    else:
        print(json.dumps(_allow()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
