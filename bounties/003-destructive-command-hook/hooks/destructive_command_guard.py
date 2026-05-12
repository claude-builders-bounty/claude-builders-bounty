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


DEFAULT_LOG_PATH = "~/.claude/hooks/blocked.log"
LOG_PATH_ENV = "CLAUDE_HOOK_BLOCK_LOG"

SHELL_BOUNDARIES = {
    ";",
    "&&",
    "||",
    "|",
    "&",
    "(",
    ")",
    "then",
    "do",
    "else",
}

RM_COMMAND_WRAPPERS = {
    "command",
    "doas",
    "env",
    "nohup",
    "sudo",
    "time",
}


def main() -> int:
    payload = read_payload()
    command = extract_bash_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    log_path = log_blocked_command(payload, command, reason)
    message = (
        f"Blocked destructive Bash command: {reason}. "
        f"The attempted command was logged to {log_path}."
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
    return 0


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    return payload if isinstance(payload, dict) else {}


def extract_bash_command(payload: dict[str, Any]) -> str | None:
    tool_name = payload.get("tool_name")
    if tool_name and tool_name != "Bash":
        return None

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command")
    return command if isinstance(command, str) and command.strip() else None


def find_block_reason(command: str) -> str | None:
    return (
        find_rm_rf(command)
        or find_force_push(command)
        or find_destructive_sql(command)
    )


def find_rm_rf(command: str) -> str | None:
    tokens = tokenize_shell(command)
    for index, token in enumerate(tokens):
        if shell_basename(token) != "rm":
            continue
        if not looks_like_command_position(tokens, index):
            continue
        if rm_flags_are_recursive_force(tokens[index + 1 :]):
            return "rm with recursive and force flags"

    for nested_command in nested_shell_c_commands(tokens):
        reason = find_rm_rf(nested_command)
        if reason:
            return reason

    return None


def tokenize_shell(command: str) -> list[str]:
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return shlex.split(command, comments=False, posix=True)


def shell_basename(token: str) -> str:
    return Path(token).name


def looks_like_command_position(tokens: list[str], index: int) -> bool:
    if index == 0:
        return True

    previous = tokens[index - 1]
    if previous in SHELL_BOUNDARIES or previous == "-exec":
        return True

    if previous in RM_COMMAND_WRAPPERS:
        return True

    if previous.startswith("-"):
        return command_wrapped_before(tokens[:index])

    return command_wrapped_before(tokens[:index])


def command_wrapped_before(prefix: list[str]) -> bool:
    """Return true after shell assignments or wrappers such as sudo -u root."""

    if not prefix:
        return False

    start = 0
    for index in range(len(prefix) - 1, -1, -1):
        if prefix[index] in SHELL_BOUNDARIES:
            start = index + 1
            break

    segment = prefix[start:]
    if not segment:
        return False

    if segment[0] in {"then", "do", "else"}:
        segment = segment[1:]
    while segment and is_assignment(segment[0]):
        segment = segment[1:]
    if not segment:
        return True

    return segment[0] in RM_COMMAND_WRAPPERS


def is_assignment(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token))


def rm_flags_are_recursive_force(tokens: list[str]) -> bool:
    recursive = False
    force = False

    for token in tokens:
        if token == "--":
            break
        if token in SHELL_BOUNDARIES:
            break
        if not token.startswith("-") or token == "-":
            continue
        if token in {"--recursive", "--dir"}:
            recursive = True
        elif token == "--force":
            force = True
        elif token.startswith("--"):
            continue
        else:
            flags = token.lstrip("-")
            recursive = recursive or "r" in flags or "R" in flags
            force = force or "f" in flags

    return recursive and force


def nested_shell_c_commands(tokens: list[str]) -> list[str]:
    nested: list[str] = []
    for index, token in enumerate(tokens):
        executable = shell_basename(token)
        if executable not in {"bash", "dash", "sh", "zsh"}:
            continue
        for option_index in range(index + 1, len(tokens)):
            option = tokens[option_index]
            if option in SHELL_BOUNDARIES:
                break
            if option == "-c" and option_index + 1 < len(tokens):
                nested.append(tokens[option_index + 1])
                break
    return nested


def find_force_push(command: str) -> str | None:
    tokens = tokenize_shell(command)
    for index in range(len(tokens) - 2):
        if shell_basename(tokens[index]) != "git":
            continue
        if not looks_like_command_position(tokens, index):
            continue
        push_index = git_subcommand_index(tokens, index)
        if push_index is None or tokens[push_index] != "push":
            continue
        push_args = tokens[push_index + 1 :]
        for arg in push_args:
            if arg in SHELL_BOUNDARIES:
                break
            if arg == "--force" or arg.startswith("--force=") or arg == "--force-with-lease":
                return "git push with force option"
            if re.fullmatch(r"-[A-Za-z]*f[A-Za-z]*", arg):
                return "git push with force option"
    return None


def git_subcommand_index(tokens: list[str], git_index: int) -> int | None:
    index = git_index + 1
    while index < len(tokens):
        token = tokens[index]
        if token in SHELL_BOUNDARIES:
            return None
        if token in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
            index += 2
            continue
        if token.startswith(("--git-dir=", "--work-tree=", "--namespace=")):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return index
    return None


def find_destructive_sql(command: str) -> str | None:
    if re.search(r"\bdrop\s+table\b", command, re.IGNORECASE):
        return "DROP TABLE statement"

    if re.search(r"\btruncate(?:\s+table)?\b", command, re.IGNORECASE):
        return "TRUNCATE statement"

    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement_tail = command[match.end() :]
        statement = re.split(r";|\n|&&|\|\|", statement_tail, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return "DELETE FROM statement without WHERE"

    return None


def log_blocked_command(payload: dict[str, Any], command: str, reason: str) -> str:
    log_path = Path(os.environ.get(LOG_PATH_ENV, DEFAULT_LOG_PATH)).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    project_path = (
        payload.get("cwd")
        or payload.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": str(project_path),
        "reason": reason,
        "command": command,
    }

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")

    return str(log_path)


if __name__ == "__main__":
    raise SystemExit(main())
