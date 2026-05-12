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


SHELL_SEPARATORS = {";", "&&", "||", "|", "(", ")"}
WRAPPER_COMMANDS = {"command", "builtin", "time"}


def _hooks_dir() -> Path:
    return Path(os.environ.get("CLAUDE_HOOKS_DIR", "~/.claude/hooks")).expanduser()


def _shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _split_commands(command: str) -> list[list[str]]:
    try:
        tokens = _shell_tokens(command)
    except ValueError:
        return []

    commands: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SHELL_SEPARATORS:
            if current:
                commands.append(current)
                current = []
            continue
        current.append(token)

    if current:
        commands.append(current)
    return commands


def _is_assignment(token: str) -> bool:
    return re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", token) is not None


def _skip_command_prefix(tokens: list[str]) -> tuple[str | None, list[str]]:
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if _is_assignment(token):
            index += 1
            continue

        if token == "sudo":
            index += 1
            while index < len(tokens) and tokens[index].startswith("-"):
                index += 1
            continue

        if token == "env":
            index += 1
            while index < len(tokens) and (
                tokens[index].startswith("-") or _is_assignment(tokens[index])
            ):
                index += 1
            continue

        if token in WRAPPER_COMMANDS:
            index += 1
            continue

        return token, tokens[index + 1 :]

    return None, []


def _rm_has_recursive_force(args: list[str]) -> bool:
    recursive = False
    force = False

    for arg in args:
        if arg == "--":
            break
        if arg == "--recursive":
            recursive = True
            continue
        if arg == "--force":
            force = True
            continue
        if arg.startswith("--"):
            continue
        if arg.startswith("-") and arg != "-":
            options = arg[1:]
            recursive = recursive or "r" in options or "R" in options
            force = force or "f" in options

    return recursive and force


def _git_has_force_push(args: list[str]) -> bool:
    if not args or args[0] != "push":
        return False

    for arg in args[1:]:
        if arg in {"-f", "--force"} or arg.startswith("--force-"):
            return True
    return False


def _shell_c_payload(command: str, args: list[str]) -> str | None:
    if Path(command).name not in {"bash", "sh", "zsh", "fish"}:
        return None

    for index, arg in enumerate(args):
        if arg == "-c" and index + 1 < len(args):
            return args[index + 1]
        if arg.startswith("-") and "c" in arg[1:] and index + 1 < len(args):
            return args[index + 1]
    return None


def _sql_block_reason(command: str) -> str | None:
    collapsed = " ".join(command.split())

    if re.search(r"\bdrop\s+table\b", collapsed, flags=re.IGNORECASE):
        return "DROP TABLE statement"

    if re.search(r"\btruncate\b", collapsed, flags=re.IGNORECASE):
        return "TRUNCATE statement"

    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        statement = command[match.start() :]
        statement = statement.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return "DELETE FROM statement without WHERE clause"

    return None


def detect_block_reason(command: str) -> str | None:
    """Return a human-readable reason if the Bash command should be blocked."""

    for tokens in _split_commands(command):
        executable, args = _skip_command_prefix(tokens)
        if not executable:
            continue

        executable_name = Path(executable).name

        if executable_name == "rm" and _rm_has_recursive_force(args):
            return "recursive forced removal (rm -rf)"

        if executable_name == "git" and _git_has_force_push(args):
            return "forced git push"

        nested_shell_command = _shell_c_payload(executable_name, args)
        if nested_shell_command:
            nested_reason = detect_block_reason(nested_shell_command)
            if nested_reason:
                return nested_reason

    return _sql_block_reason(command)


def _log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    log_path = _hooks_dir() / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _deny_output(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: "
                f"{reason}. Review the command and request explicit user approval "
                "before trying a safer alternative."
            ),
        }
    }


def handle_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    if payload.get("hook_event_name") != "PreToolUse":
        return None
    if payload.get("tool_name") != "Bash":
        return None

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return None

    reason = detect_block_reason(command)
    if reason is None:
        return None

    project_path = str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or "")
    _log_blocked_attempt(command, project_path, reason)
    return _deny_output(reason)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    output = handle_event(payload)
    if output is not None:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
