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
from typing import Iterable


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
SHELL_SEPARATORS = {";", "&&", "||", "|", "\n"}
COMMAND_WRAPPERS = {"sudo", "doas", "command", "builtin", "time"}

DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def command_segments(tokens: Iterable[str]) -> Iterable[list[str]]:
    current: list[str] = []
    for token in tokens:
        if token in SHELL_SEPARATORS:
            if current:
                yield current
                current = []
            continue
        current.append(token)
    if current:
        yield current


def is_assignment(token: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*", token))


def strip_env_args(segment: list[str]) -> list[str]:
    segment = segment[1:]
    while segment:
        token = segment[0]
        if is_assignment(token):
            segment = segment[1:]
            continue
        if token == "--":
            segment = segment[1:]
            break
        if token in {"-i", "--ignore-environment"}:
            segment = segment[1:]
            continue
        if token in {"-u", "--unset"} and len(segment) > 1:
            segment = segment[2:]
            continue
        if token.startswith("--unset="):
            segment = segment[1:]
            continue
        break
    return segment


def strip_command_prefix(segment: list[str]) -> list[str]:
    while segment:
        while segment and is_assignment(segment[0]):
            segment = segment[1:]
        if not segment:
            return segment

        command_name = os.path.basename(segment[0])
        if command_name in COMMAND_WRAPPERS:
            segment = segment[1:]
            if segment and segment[0] == "--":
                segment = segment[1:]
            continue
        if command_name == "env":
            segment = strip_env_args(segment)
            continue
        return segment
    return segment


def rm_has_recursive_force_options(args: Iterable[str]) -> bool:
    has_recursive = False
    has_force = False

    for arg in args:
        if arg == "--":
            break
        if not arg.startswith("-") or arg == "-":
            continue
        if arg in {"--recursive", "--dir"}:
            has_recursive = True
            continue
        if arg == "--force":
            has_force = True
            continue
        if arg.startswith("--"):
            continue

        short_opts = arg.lstrip("-")
        if "r" in short_opts or "R" in short_opts:
            has_recursive = True
        if "f" in short_opts:
            has_force = True

    return has_recursive and has_force


def contains_rm_rf(command: str) -> bool:
    try:
        tokens = tokenize(command)
    except ValueError:
        return bool(re.search(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f|rm\s+-[A-Za-z]*f[A-Za-z]*r", command))

    for segment in command_segments(tokens):
        segment = strip_command_prefix(segment)
        if segment and os.path.basename(segment[0]) == "rm" and rm_has_recursive_force_options(segment[1:]):
            return True

    return False


def skip_git_global_option(args: list[str], index: int) -> int:
    option = args[index]
    if option in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
        return index + 2
    if option in {
        "--bare",
        "--no-pager",
        "--no-replace-objects",
        "--literal-pathspecs",
        "--glob-pathspecs",
        "--noglob-pathspecs",
        "--icase-pathspecs",
        "--no-optional-locks",
        "-P",
    }:
        return index + 1
    if option.startswith(("--git-dir=", "--work-tree=", "--namespace=")):
        return index + 1
    return index


def git_push_has_force(args: Iterable[str]) -> bool:
    for arg in args:
        if arg == "--":
            continue
        if arg.startswith("--force"):
            return True
        if arg.startswith("-") and not arg.startswith("--") and "f" in arg.lstrip("-"):
            return True
    return False


def contains_git_force_push(command: str) -> bool:
    try:
        tokens = tokenize(command)
    except ValueError:
        return bool(
            re.search(
                r"(?:^|[;&|]\s*)git\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?(?:=\S+)?|-f)\b",
                command,
                re.IGNORECASE,
            )
        )

    for segment in command_segments(tokens):
        segment = strip_command_prefix(segment)
        if not segment or os.path.basename(segment[0]) != "git":
            continue

        index = 1
        while index < len(segment):
            next_index = skip_git_global_option(segment, index)
            if next_index != index:
                index = next_index
                continue
            break

        if index < len(segment) and segment[index] == "push":
            if git_push_has_force(segment[index + 1 :]):
                return True
    return False


def contains_delete_without_where(command: str) -> bool:
    statements = re.split(r";|&&|\|\|", command)
    for statement in statements:
        match = DELETE_FROM_RE.search(statement)
        if not match:
            continue
        tail = statement[match.end() :]
        if not re.search(r"\bwhere\b", tail, re.IGNORECASE):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    if contains_rm_rf(command):
        return "Blocked destructive rm command using recursive and force options."
    if contains_git_force_push(command):
        return "Blocked force push command."
    if DROP_TABLE_RE.search(command):
        return "Blocked destructive SQL DROP TABLE command."
    if TRUNCATE_RE.search(command):
        return "Blocked destructive SQL TRUNCATE command."
    if contains_delete_without_where(command):
        return "Blocked SQL DELETE FROM command without a WHERE clause."
    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        deny("Blocked Bash command because the hook received invalid JSON.")
        return 0

    if event.get("tool_name") != "Bash":
        return 0

    command = event.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    project_path = (
        event.get("cwd")
        or event.get("project_path")
        or event.get("workspace")
        or os.getcwd()
    )
    log_block(command, str(project_path), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
