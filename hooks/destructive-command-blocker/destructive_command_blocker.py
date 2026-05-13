#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads the Claude Code hook JSON payload from stdin, inspects Bash tool
commands, and emits a structured deny decision when a dangerous command is
found. Blocked attempts are appended to ~/.claude/hooks/blocked.log.
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

DANGEROUS_MESSAGE = (
    "Blocked destructive Bash command before execution. This command matched "
    "a configured safety rule: {reason}. Review the command and use a safer, "
    "more targeted alternative before retrying."
)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*(?=\n|$)", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return sql


def has_delete_without_where(command: str) -> bool:
    sql = normalize_space(strip_sql_comments(command)).lower()
    for match in re.finditer(r"\bdelete\s+from\s+[`\"\[]?[\w.\]-]+[`\"\]]?", sql):
        tail = sql[match.end() :]
        stop_positions = [pos for pos in (tail.find(";"), tail.find("&&"), tail.find("||")) if pos != -1]
        statement_tail = tail[: min(stop_positions)] if stop_positions else tail
        if not re.search(r"\bwhere\b", statement_tail):
            return True
    return False


def shell_tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return command.split()


def split_shell_commands(tokens: list[str]) -> list[list[str]]:
    commands: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in {";", "&&", "||", "|", "&", "(", ")"}:
            if current:
                commands.append(current)
                current = []
        else:
            current.append(token)
    if current:
        commands.append(current)
    return commands


def strip_command_prefixes(tokens: list[str]) -> list[str]:
    remaining = tokens[:]
    while remaining:
        head = remaining[0]
        if "=" in head and not head.startswith("-") and head.split("=", 1)[0].isidentifier():
            remaining = remaining[1:]
            continue
        if head in {"sudo", "command", "builtin", "time"}:
            remaining = remaining[1:]
            continue
        if head == "env":
            remaining = remaining[1:]
            # `env` supports option-only prefixes before the command. Keep this
            # small but practical so variants such as `env -i FOO=bar rm -rf x`
            # are inspected as the underlying `rm` invocation.
            env_options_with_value = {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}
            while remaining:
                if "=" in remaining[0] and not remaining[0].startswith("-"):
                    remaining = remaining[1:]
                    continue
                if remaining[0] in {"-i", "--ignore-environment", "-0", "--null"}:
                    remaining = remaining[1:]
                    continue
                if remaining[0] in env_options_with_value:
                    remaining = remaining[2:] if len(remaining) > 1 else []
                    continue
                if any(remaining[0].startswith(prefix + "=") for prefix in env_options_with_value if prefix.startswith("--")):
                    remaining = remaining[1:]
                    continue
                break
            continue
        return remaining
    return remaining


def inspect_rm_tokens(tokens: list[str]) -> bool:
    flags = "".join(t[1:] for t in tokens[1:] if t.startswith("-") and not t.startswith("--"))
    long_flags = {t for t in tokens[1:] if t.startswith("--")}
    has_recursive = "r" in flags or "R" in flags or "--recursive" in long_flags
    has_force = "f" in flags or "--force" in long_flags
    return has_recursive and has_force


def git_subcommand_index(tokens: list[str]) -> int | None:
    """Return the index of the git subcommand, skipping global options.

    Git accepts options before the subcommand (for example
    `git -c push.default=simple push --force-with-lease`). The hook should still
    block destructive push variants even when contributors use those options.
    """
    index = 1
    options_with_value = {"-c", "--config-env", "--git-dir", "--work-tree", "--namespace"}
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token in options_with_value:
            index += 2
            continue
        if any(token.startswith(prefix + "=") for prefix in options_with_value if prefix.startswith("--")):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return index
    return index if index < len(tokens) else None


def inspect_git_tokens(tokens: list[str]) -> bool:
    subcommand_index = git_subcommand_index(tokens)
    if subcommand_index is None or tokens[subcommand_index] != "push":
        return False
    return any(
        t in {"--force", "--force-with-lease", "-f"}
        or t.startswith("--force-with-lease=")
        or t.startswith("+refs/")
        or t.startswith("+")
        for t in tokens[subcommand_index + 1 :]
    )


def inspect_shell_commands(command: str) -> str | None:
    for tokens in split_shell_commands(shell_tokens(command)):
        tokens = strip_command_prefixes(tokens)
        if not tokens:
            continue

        executable = Path(tokens[0]).name
        if executable in {"bash", "sh", "zsh"} and "-c" in tokens:
            index = tokens.index("-c")
            if index + 1 < len(tokens):
                nested = detect_destructive_pattern(tokens[index + 1])
                if nested:
                    return nested

        if executable == "rm" and inspect_rm_tokens(tokens):
            return "rm recursive+force (for example rm -rf)"

        if executable == "git" and inspect_git_tokens(tokens):
            return "git push --force"

    return None


def detect_destructive_pattern(command: str) -> str | None:
    compact = normalize_space(command)
    lowered = compact.lower()

    # Required shell patterns. Token-aware checks catch command variants while
    # avoiding harmless documentation/search strings such as `echo rm -rf`.
    shell_reason = inspect_shell_commands(command)
    if shell_reason:
        return shell_reason

    if re.search(r"\bdrop\s+table\b", lowered):
        return "DROP TABLE"

    if re.search(r"\btruncate\b", lowered):
        return "TRUNCATE"

    if has_delete_without_where(command):
        return "DELETE FROM without a WHERE clause"

    return None


def extract_command(payload: dict[str, Any]) -> str | None:
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}

    if tool_name and tool_name.lower() not in {"bash", "shell"}:
        return None

    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or tool_input.get("script")
        if isinstance(command, str):
            return command
    elif isinstance(tool_input, str):
        return tool_input

    # Be permissive for local tests or format changes.
    command = payload.get("command") or payload.get("cmd")
    return command if isinstance(command, str) else None


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(tool_input, dict):
        for key in ("cwd", "project_path", "projectPath"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value
    return os.getcwd()


def log_blocked(command: str, path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    message = DANGEROUS_MESSAGE.format(reason=reason)
    print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": message}))


def allow() -> None:
    print(json.dumps({"permissionDecision": "allow"}))


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Malformed hook input should not break normal Claude Code usage.
        allow()
        return 0

    command = extract_command(payload)
    if not command:
        allow()
        return 0

    reason = detect_destructive_pattern(command)
    if not reason:
        allow()
        return 0

    path = project_path(payload)
    log_blocked(command, path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
