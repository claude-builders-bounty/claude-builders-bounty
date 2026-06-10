#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

WRAPPER_COMMANDS = {
    "builtin",
    "command",
    "env",
    "nice",
    "nohup",
    "sudo",
    "time",
}

SHELL_SEPARATORS = {";", "&&", "||", "|", "\n"}
COMMAND_SEPARATORS = {";", "&&", "||", "\n"}

REMOTE_FETCH_COMMANDS = {"curl", "wget"}
SHELL_COMMANDS = {"bash", "fish", "sh", "zsh"}

SQL_CLIENT_TOKENS = {
    "clickhouse-client",
    "duckdb",
    "mariadb",
    "mysql",
    "psql",
    "sqlite3",
    "sqlcmd",
}

SQL_TOOL_TOKENS = {
    "prisma",
    "supabase",
    "turso",
    "wrangler",
}

TRUNCATE_STATEMENT_RE = re.compile(
    r"\btruncate\s+(?:table\s+)?(?:[`\"']?[A-Za-z_][\w$.]*[`\"']?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BlockReason:
    code: str
    message: str


def load_hook_input(stdin_text: str) -> dict[str, Any]:
    if not stdin_text.strip():
        return {}

    try:
        payload = json.loads(stdin_text)
    except json.JSONDecodeError:
        return {"tool_input": {"command": stdin_text.strip()}}

    return payload if isinstance(payload, dict) else {}


def nested_get(data: dict[str, Any], *path: str) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_command(payload: dict[str, Any], argv: list[str] | None = None) -> str:
    candidates: list[Any] = [
        nested_get(payload, "tool_input", "command"),
        nested_get(payload, "tool_input", "cmd"),
        nested_get(payload, "tool_input", "input"),
        nested_get(payload, "tool_input", "args"),
        payload.get("command"),
        payload.get("cmd"),
        payload.get("bash_command"),
    ]

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        if isinstance(candidate, list) and candidate:
            return " ".join(str(part) for part in candidate).strip()

    if argv:
        return " ".join(argv).strip()

    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    candidates = [
        nested_get(payload, "tool_input", "cwd"),
        nested_get(payload, "tool_input", "project_path"),
        nested_get(payload, "tool_input", "projectPath"),
        payload.get("cwd"),
        payload.get("project_path"),
        payload.get("projectPath"),
        payload.get("workspace"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return os.environ.get("PWD", "")


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name") or payload.get("toolName") or payload.get("name")
    return not tool_name or tool_name == "Bash"


def shell_tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except (TypeError, ValueError):
        try:
            return shlex.split(command, comments=False, posix=True)
        except ValueError:
            return command.replace("\n", " ; ").split()


def split_shell_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []

    for token in tokens:
        if token in SHELL_SEPARATORS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)

    if current:
        segments.append(current)

    return segments


def split_command_groups(tokens: list[str]) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []

    for token in tokens:
        if token in COMMAND_SEPARATORS:
            if current:
                groups.append(current)
                current = []
            continue
        current.append(token)

    if current:
        groups.append(current)

    return groups


def split_pipeline_stages(tokens: list[str]) -> list[list[str]]:
    stages: list[list[str]] = []
    current: list[str] = []

    for token in tokens:
        if token == "|":
            if current:
                stages.append(current)
                current = []
            continue
        current.append(token)

    if current:
        stages.append(current)

    return stages


def command_name(token: str) -> str:
    return token.rsplit("/", 1)[-1]


def strip_wrappers(tokens: list[str]) -> list[str]:
    remaining = list(tokens)

    while remaining:
        head = remaining[0]

        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*", head):
            remaining.pop(0)
            continue

        if head == "sudo":
            remaining.pop(0)
            while remaining and remaining[0].startswith("-"):
                option = remaining.pop(0)
                if option in {"-u", "-g", "-h", "-p"} and remaining:
                    remaining.pop(0)
            continue

        if head == "env":
            remaining.pop(0)
            while remaining:
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*", remaining[0]):
                    remaining.pop(0)
                    continue
                if remaining[0].startswith("-"):
                    remaining.pop(0)
                    continue
                break
            continue

        if head in WRAPPER_COMMANDS:
            remaining.pop(0)
            continue

        break

    return remaining


def git_invocation(tokens: list[str]) -> tuple[str, list[str], bool] | None:
    stripped = strip_wrappers(tokens)
    if not stripped or command_name(stripped[0]) != "git":
        return None

    args = stripped[1:]
    force_push_config = False
    index = 0

    while index < len(args) and args[index].startswith("-"):
        option = args[index]

        if option == "-c" and index + 1 < len(args):
            key_value = args[index + 1].lower()
            if key_value.startswith("push.force="):
                force_push_config = key_value.split("=", 1)[1] in {"1", "true", "yes", "on"}
            index += 2
            continue

        if option in {"-C", "--git-dir", "--work-tree", "--namespace"} and index + 1 < len(args):
            index += 2
            continue

        if option.startswith(("--git-dir=", "--work-tree=", "--namespace=")):
            index += 1
            continue

        index += 1

    if index >= len(args):
        return None

    return args[index], args[index + 1 :], force_push_config


def rm_has_recursive_force_flags(tokens: list[str]) -> bool:
    has_recursive = False
    has_force = False

    for token in tokens[1:]:
        if token == "--":
            break
        if not token.startswith("-") or token == "-":
            continue

        if token in {"--recursive", "--dir"}:
            has_recursive = True
        elif token == "--force":
            has_force = True
        elif token.startswith("--"):
            continue
        else:
            flags = token.lstrip("-")
            has_recursive = has_recursive or "r" in flags or "R" in flags
            has_force = has_force or "f" in flags

    return has_recursive and has_force


def has_force_push(tokens: list[str]) -> bool:
    parsed = git_invocation(tokens)
    if parsed is None:
        return False

    subcommand, push_args, force_push_config = parsed
    if subcommand != "push":
        return False

    if force_push_config:
        return True

    for arg in push_args:
        if arg == "--":
            continue
        if arg in {"-f", "--force", "--force-with-lease", "--force-if-includes"}:
            return True
        if arg.startswith("--force"):
            return True
        if arg.startswith("+") and arg != "+":
            return True
    return False


def has_hard_reset(tokens: list[str]) -> bool:
    parsed = git_invocation(tokens)
    if parsed is None:
        return False

    subcommand, reset_args, _force_push_config = parsed
    return subcommand == "reset" and "--hard" in reset_args


def has_block_device_write(tokens: list[str]) -> bool:
    stripped = strip_wrappers(tokens)
    if not stripped:
        return False

    name = command_name(stripped[0])
    args = stripped[1:]

    if name == "dd":
        return any(arg.startswith("of=/dev/") for arg in args)

    if name == "wipefs" or name.startswith("mkfs"):
        return any(arg.startswith("/dev/") for arg in args)

    return False


def has_remote_script_pipe(tokens: list[str]) -> bool:
    for group in split_command_groups(tokens):
        stages = split_pipeline_stages(group)
        for index, stage in enumerate(stages[:-1]):
            stripped_stage = strip_wrappers(stage)
            if not stripped_stage or command_name(stripped_stage[0]) not in REMOTE_FETCH_COMMANDS:
                continue

            next_stage = strip_wrappers(stages[index + 1])
            if next_stage and command_name(next_stage[0]) in SHELL_COMMANDS:
                return True

    return False


def detect_destructive_shell(command: str) -> BlockReason | None:
    tokens = shell_tokens(command)

    if has_remote_script_pipe(tokens):
        return BlockReason(
            "remote_script_pipe",
            "piping a downloaded script directly into a shell can execute unreviewed remote code",
        )

    for segment in split_shell_segments(tokens):
        stripped = strip_wrappers(segment)
        if not stripped:
            continue

        if command_name(stripped[0]) == "rm" and rm_has_recursive_force_flags(stripped):
            return BlockReason(
                "rm_recursive_force",
                "rm with both recursive and force flags can delete large directory trees without confirmation",
            )

        if has_force_push(segment):
            return BlockReason(
                "git_force_push",
                "git push with force flags can overwrite remote history",
            )

        if has_hard_reset(segment):
            return BlockReason(
                "git_reset_hard",
                "git reset --hard can discard local work without confirmation",
            )

        if has_block_device_write(segment):
            return BlockReason(
                "block_device_write",
                "writing directly to block devices can destroy disks or filesystems",
            )

    return None


def strip_sql_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"--[^\n\r]*", " ", text)
    return text


def split_sql_statements(text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False

    for char in text:
        current.append(char)

        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if quote:
            if char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
            continue

        if char == ";":
            statements.append("".join(current))
            current = []

    if current:
        statements.append("".join(current))

    return statements


def starts_with_sql(command: str) -> bool:
    stripped = command.lstrip()
    if re.match(r"(drop\s+table|delete\s+from)\b", stripped, re.IGNORECASE):
        return True
    return bool(TRUNCATE_STATEMENT_RE.match(stripped))


def has_sql_execution_context(command: str) -> bool:
    if starts_with_sql(command):
        return True

    tokens = [token.lower() for token in shell_tokens(command)]
    if any(token in SQL_CLIENT_TOKENS for token in tokens):
        return True
    return any(token in SQL_TOOL_TOKENS for token in tokens)


def detect_destructive_sql(command: str) -> BlockReason | None:
    if not has_sql_execution_context(command):
        return None

    searchable = strip_sql_comments(command)

    if re.search(r"\bdrop\s+table\b", searchable, re.IGNORECASE):
        return BlockReason("drop_table", "DROP TABLE removes a database table")

    if TRUNCATE_STATEMENT_RE.search(searchable):
        return BlockReason("truncate", "TRUNCATE removes all rows from a table")

    for statement in split_sql_statements(searchable):
        for match in re.finditer(r"\bdelete\s+from\b", statement, re.IGNORECASE):
            remainder = statement[match.end() :]
            if not re.search(r"\bwhere\b", remainder, re.IGNORECASE):
                return BlockReason(
                    "delete_without_where",
                    "DELETE FROM without a WHERE clause can remove every row in a table",
                )

    return None


def evaluate_command(command: str) -> BlockReason | None:
    return detect_destructive_shell(command) or detect_destructive_sql(command)


def truncate_for_message(command: str, limit: int = 500) -> str:
    normalized = " ".join(command.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def append_block_log(command: str, project_path: str, reason: BlockReason) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "project_path": project_path,
        "command": command,
        "reason": reason.message,
        "reason_code": reason.code,
    }

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except OSError:
        # Blocking the command matters more than the audit trail if the log
        # directory is temporarily unavailable.
        pass


def deny_output(reason: BlockReason, command: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: "
                f"{reason.message}. Attempted command: {truncate_for_message(command)}"
            ),
        }
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    payload = load_hook_input(sys.stdin.read())

    if not is_bash_tool(payload):
        return 0

    command = extract_command(payload, argv)
    if not command:
        return 0

    reason = evaluate_command(command)
    if reason is None:
        return 0

    append_block_log(command, extract_project_path(payload), reason)
    print(json.dumps(deny_output(reason, command), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
