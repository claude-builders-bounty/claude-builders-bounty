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


BLOCK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
SHELL_COMMANDS = {"bash", "sh", "zsh", "dash", "ksh"}
COMMAND_SEPARATORS = {";", "&&", "||", "|", "\n"}


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def command_name(token: str) -> str:
    return token.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]


def option_letters(option: str) -> str:
    return option[1:] if option.startswith("-") and not option.startswith("--") else ""


def has_recursive_force_rm(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if command_name(token) != "rm":
            continue

        has_recursive = False
        has_force = False
        for arg in tokens[index + 1 :]:
            if arg in COMMAND_SEPARATORS:
                break
            if arg == "--":
                break
            if not arg.startswith("-"):
                continue

            if arg in {"--recursive", "--dir"}:
                has_recursive = True
            elif arg == "--force":
                has_force = True
            else:
                letters = option_letters(arg)
                has_recursive = has_recursive or "r" in letters.lower()
                has_force = has_force or "f" in letters.lower()

            if has_recursive and has_force:
                return True

    return False


def has_force_git_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if command_name(token) != "git":
            continue

        saw_push = False
        for arg in tokens[index + 1 :]:
            if arg in COMMAND_SEPARATORS:
                break
            if not saw_push:
                if arg == "push":
                    saw_push = True
                continue
            if arg in {"--force", "-f"}:
                return True

    return False


def sql_delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        statement_tail = command[match.end() :].split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement_tail, flags=re.IGNORECASE):
            return True
    return False


def nested_shell_commands(tokens: list[str]) -> list[str]:
    nested: list[str] = []
    for index, token in enumerate(tokens[:-1]):
        if command_name(token) in SHELL_COMMANDS and tokens[index + 1] == "-c":
            if index + 2 < len(tokens):
                nested.append(tokens[index + 2])
    return nested


def find_block_reason(command: str, depth: int = 0) -> str | None:
    if not command.strip():
        return None

    try:
        tokens = tokenize(command)
    except ValueError as error:
        return f"Blocked Bash command because it could not be parsed safely: {error}"

    if has_recursive_force_rm(tokens):
        return "Blocked destructive Bash command: recursive forced removal (`rm -rf`) is not allowed."
    if has_force_git_push(tokens):
        return "Blocked destructive Bash command: force-pushing with `git push --force` is not allowed."
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "Blocked destructive database command: `DROP TABLE` is not allowed."
    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return "Blocked destructive database command: `TRUNCATE` is not allowed."
    if sql_delete_without_where(command):
        return "Blocked destructive database command: `DELETE FROM` without a WHERE clause is not allowed."

    if depth < 2:
        for nested in nested_shell_commands(tokens):
            reason = find_block_reason(nested, depth + 1)
            if reason:
                return reason

    return None


def project_path(event: dict) -> str:
    return (
        event.get("cwd")
        or event.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def log_block(command: str, project: str, reason: str) -> None:
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project,
        "reason": reason,
    }
    with BLOCK_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        deny(f"Blocked Bash command because hook input was not valid JSON: {error}")
        return 0

    if event.get("tool_name") != "Bash":
        return 0

    command = str(event.get("tool_input", {}).get("command", ""))
    reason = find_block_reason(command)
    if not reason:
        return 0

    project = project_path(event)
    log_block(command, project, reason)
    deny(f"{reason} Project: {project}. The attempt was logged to {BLOCK_LOG}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
