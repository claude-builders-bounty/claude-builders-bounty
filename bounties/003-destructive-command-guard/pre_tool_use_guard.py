#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive shell and SQL commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


DEFAULT_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _strip_sql_comments(command: str) -> str:
    command = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    command = re.sub(r"--[^\n\r]*", " ", command)
    return command


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def _contains_rm_rf(command: str) -> bool:
    tokens = _shell_tokens(command)
    for index, token in enumerate(tokens):
        if token not in {"rm", "/bin/rm", "sudo"}:
            continue

        rm_index = index
        if token == "sudo" and index + 1 < len(tokens) and tokens[index + 1].endswith("rm"):
            rm_index = index + 1
        elif token == "sudo":
            continue

        flags = ""
        for arg in tokens[rm_index + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-") or arg == "-":
                continue
            if arg.startswith("--"):
                flags += {
                    "--recursive": "r",
                    "--force": "f",
                    "--no-preserve-root": "x",
                }.get(arg, "")
            else:
                flags += arg.lstrip("-")
        if "r" in flags and "f" in flags:
            return True
    return False


def _contains_force_push(command: str) -> bool:
    tokens = _shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "git":
            continue
        if index + 1 >= len(tokens) or tokens[index + 1] != "push":
            continue
        args = tokens[index + 2 :]
        return any(arg in {"--force", "-f", "--force-with-lease", "--force-if-includes"} for arg in args)
    return False


def _contains_drop_table(command: str) -> bool:
    normalized = _collapse_whitespace(_strip_sql_comments(command)).lower()
    return bool(re.search(r"\bdrop\s+table\b", normalized))


def _contains_truncate(command: str) -> bool:
    normalized = _collapse_whitespace(_strip_sql_comments(command)).lower()
    return bool(re.search(r"\btruncate(?:\s+table)?\s+[a-zA-Z0-9_\".`]+", normalized))


def _delete_statements_without_where(command: str) -> list[str]:
    cleaned = _strip_sql_comments(command)
    statements = [part.strip() for part in re.split(r";+", cleaned) if part.strip()]
    unsafe: list[str] = []
    for statement in statements:
        normalized = _collapse_whitespace(statement).lower()
        if re.search(r"\bdelete\s+from\b", normalized) and not re.search(r"\bwhere\b", normalized):
            unsafe.append(statement)
    return unsafe


def find_block_reason(command: str) -> str | None:
    if _contains_rm_rf(command):
        return "Blocked destructive shell command: recursive forced deletion via rm."
    if _contains_force_push(command):
        return "Blocked destructive git command: force push can rewrite shared history."
    if _contains_drop_table(command):
        return "Blocked destructive SQL command: DROP TABLE requires explicit human approval."
    if _contains_truncate(command):
        return "Blocked destructive SQL command: TRUNCATE removes all rows."
    if _delete_statements_without_where(command):
        return "Blocked destructive SQL command: DELETE FROM without a WHERE clause."
    return None


def read_hook_input(stdin: str) -> tuple[str, str, str]:
    try:
        payload: dict[str, Any] = json.loads(stdin or "{}")
    except json.JSONDecodeError:
        return stdin, "", os.getcwd()

    tool_name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    command = ""
    if isinstance(tool_input, dict):
        command = str(tool_input.get("command") or tool_input.get("cmd") or tool_input.get("query") or "")
    project_path = str(payload.get("cwd") or payload.get("project_path") or os.getcwd())
    return command, tool_name, project_path


def append_block_log(log_path: Path, command: str, project_path: str, reason: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def decision_payload(blocked: bool, reason: str | None) -> dict[str, Any]:
    if not blocked:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Block destructive Claude Code Bash commands.")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="Path for blocked attempt log.")
    parser.add_argument(
        "--legacy-exit-code",
        action="store_true",
        help="Exit 2 and write the block reason to stderr instead of returning JSON.",
    )
    args = parser.parse_args()

    command, tool_name, project_path = read_hook_input(sys.stdin.read())
    if tool_name and tool_name.lower() not in {"bash", "shell"}:
        print(json.dumps(decision_payload(False, None)))
        return 0

    reason = find_block_reason(command)
    if not reason:
        print(json.dumps(decision_payload(False, None)))
        return 0

    append_block_log(args.log, command, project_path, reason)
    if args.legacy_exit_code:
        print(reason, file=sys.stderr)
        return 2

    print(json.dumps(decision_payload(True, reason)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
