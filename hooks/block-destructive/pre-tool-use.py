#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
SEGMENT_DELIMITERS = {";", "&&", "||", "|", "&"}
WRAPPER_COMMANDS = {"sudo", "env", "command", "builtin", "nohup", "time"}
SAFE_TEXT_COMMANDS = {"echo", "printf"}
SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "duckdb", "sqlcmd"}
SQL_INLINE_FLAGS = {"-c", "-e", "--command", "--execute", "-Q", "-q"}
class Decision:
    def __init__(self, reason: str) -> None:
        self.reason = reason


def load_payload(stdin: str) -> dict:
    if not stdin.strip():
        return {}
    data = json.loads(stdin)
    if not isinstance(data, dict):
        raise ValueError("Hook payload must be a JSON object")
    return data


def split_shell_segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = list(lexer)

    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SEGMENT_DELIMITERS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def unwrap_segment(segment: Iterable[str]) -> list[str]:
    tokens = list(segment)
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", token):
            idx += 1
            continue
        if token in WRAPPER_COMMANDS:
            idx += 1
            continue
        break
    return tokens[idx:]


def token_has_recursive_force(token: str) -> bool:
    if not token.startswith("-") or token.startswith("--"):
        return token == "--force"
    flags = set(token[1:])
    return "r" in flags and "f" in flags


def token_has_force_push_flag(token: str) -> bool:
    if token == "--force":
        return True
    if token.startswith("-") and not token.startswith("--"):
        return "f" in set(token[1:])
    return False


def extract_sql_statements(command_name: str, tokens: list[str]) -> list[str]:
    lowered = command_name.lower()
    if lowered in SAFE_TEXT_COMMANDS:
        return []

    if lowered in SQL_CLIENTS:
        statements: list[str] = []
        idx = 1
        while idx < len(tokens):
            token = tokens[idx]
            if token in SQL_INLINE_FLAGS and idx + 1 < len(tokens):
                statements.append(tokens[idx + 1])
                idx += 2
                continue
            idx += 1
        if lowered == "sqlite3" and len(tokens) >= 3:
            statements.append(tokens[-1])
        return statements

    if lowered in {"drop", "truncate", "delete"}:
        return [" ".join(tokens)]

    return []


def delete_without_where(statement: str) -> bool:
    lowered = statement.lower()
    for match in re.finditer(r"\bdelete\s+from\b", lowered):
        tail = lowered[match.end() :]
        boundary = len(tail)
        for separator in (";", "&&", "||", "|"):
            pos = tail.find(separator)
            if pos != -1:
                boundary = min(boundary, pos)
        if " where " not in f" {tail[:boundary]} ":
            return True
    return False


def inspect_command(command: str) -> Decision | None:
    raw_segments = split_shell_segments(command)
    for raw_segment in raw_segments:
        segment = unwrap_segment(raw_segment)
        if not segment:
            continue

        command_name = segment[0].lower()

        if command_name == "rm":
            if any(token_has_recursive_force(token) for token in segment[1:]):
                return Decision("Blocked destructive filesystem command: rm -rf")

        if command_name == "git" and len(segment) >= 2 and segment[1].lower() == "push":
            if any(token_has_force_push_flag(token) for token in segment[2:]):
                return Decision("Blocked destructive git command: git push --force")

        for statement in extract_sql_statements(command_name, segment):
            normalized = re.sub(r"\s+", " ", statement.strip())
            lowered = normalized.lower()
            if re.search(r"\bdrop\s+table\b", lowered):
                return Decision("Blocked destructive SQL command: DROP TABLE")
            if re.search(r"\btruncate\b", lowered):
                return Decision("Blocked destructive SQL command: TRUNCATE")
            if delete_without_where(normalized):
                return Decision("Blocked destructive SQL command: DELETE FROM without WHERE")

    return None


def append_log(command: str, project_path: str, reason: str) -> None:
    blocked_log = Path("~/.claude/hooks/blocked.log").expanduser()
    blocked_log.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command.strip(),
        "project_path": project_path,
        "reason": reason,
    }
    with blocked_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def build_deny_response(reason: str, command: str, project_path: str) -> str:
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"{reason}. Command blocked before execution. "
                    f"Attempted command: {command.strip()}. "
                    f"Project path: {project_path}"
                ),
            }
        },
        ensure_ascii=True,
    )


def main() -> int:
    payload = load_payload(sys.stdin.read())
    if not payload or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    command = str(tool_input.get("command") or tool_input.get("cmd") or "").strip()
    if not command:
        return 0

    project_path = str(
        payload.get("cwd")
        or tool_input.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )

    decision = inspect_command(command)
    if decision is None:
        return 0

    append_log(command, project_path, decision.reason)
    print(build_deny_response(decision.reason, command, project_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
