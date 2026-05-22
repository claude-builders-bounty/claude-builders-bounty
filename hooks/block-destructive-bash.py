#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\s+[a-zA-Z_][\w.]*", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)

COMMAND_SEPARATORS = {"&&", "||", ";", "|", "&"}
RM_RECURSIVE_FLAGS = {"r", "R"}


def _basename(token: str) -> str:
    return token.rsplit("/", 1)[-1]


def _split_shell(command: str) -> List[str]:
    try:
        return shlex.split(command, comments=True, posix=True)
    except ValueError:
        return command.split()


def _option_letters(option: str) -> Set[str]:
    if not option.startswith("-") or option == "-":
        return set()
    if option.startswith("--"):
        return set()
    return set(option[1:])


def _has_rm_rf(tokens: List[str]) -> bool:
    for index, token in enumerate(tokens):
        if _basename(token) != "rm":
            continue

        has_recursive = False
        has_force = False

        for candidate in tokens[index + 1 :]:
            if candidate in COMMAND_SEPARATORS:
                break
            if candidate == "--":
                break

            if candidate in {"--recursive", "--dir"}:
                has_recursive = True
            elif candidate == "--force":
                has_force = True
            elif candidate.startswith("-"):
                letters = _option_letters(candidate)
                has_recursive = has_recursive or bool(letters & RM_RECURSIVE_FLAGS)
                has_force = has_force or "f" in letters

            if has_recursive and has_force:
                return True

    return False


def _has_force_push(tokens: List[str]) -> bool:
    for index, token in enumerate(tokens):
        if _basename(token) != "git":
            continue

        cursor = index + 1
        while cursor < len(tokens) and tokens[cursor] not in COMMAND_SEPARATORS:
            current = tokens[cursor]

            if current == "push":
                for candidate in tokens[cursor + 1 :]:
                    if candidate in COMMAND_SEPARATORS:
                        break
                    if candidate in {"--force", "-f"} or candidate.startswith("--force="):
                        return True
                    if candidate == "--force-with-lease" or candidate.startswith("--force-with-lease="):
                        return True
                    if candidate.startswith("-") and "f" in _option_letters(candidate):
                        return True
                break

            if current in {"-C", "--git-dir", "--work-tree"}:
                cursor += 2
            else:
                cursor += 1

    return False


def _has_destructive_sql(command: str, tokens: List[str]) -> Optional[str]:
    if DROP_TABLE_RE.search(command):
        return "DROP TABLE statements can destroy schema or data."

    first_token = _basename(tokens[0]).lower() if tokens else ""
    is_file_truncate = first_token == "truncate" and len(tokens) > 1 and tokens[1].startswith("-")
    if not is_file_truncate and TRUNCATE_RE.search(command):
        return "TRUNCATE statements can remove all rows from a table."

    for statement in command.split(";"):
        match = DELETE_FROM_RE.search(statement)
        if match and not WHERE_RE.search(statement[match.end() :]):
            return "DELETE FROM without a WHERE clause can remove every matching row."

    return None


def find_block_reason(command: str) -> Optional[str]:
    tokens = _split_shell(command)

    if _has_rm_rf(tokens):
        return "rm with both recursive and force flags is blocked."

    if _has_force_push(tokens):
        return "git push --force can overwrite remote history."

    return _has_destructive_sql(command, tokens)


def _project_path(payload: Dict[str, object]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "command": command,
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }

    with (log_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _deny(reason: str, command: str) -> None:
    message = (
        "Blocked destructive Bash command before execution: "
        f"{reason} Command: {command!r}"
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_blocked_attempt(command, project_path, reason)
    _deny(reason, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
