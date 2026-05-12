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
from typing import Any, Iterable


HOOK_EVENT_NAME = "PreToolUse"

COMMAND_SEPARATORS = {
    ";",
    "&",
    "&&",
    "|",
    "|&",
    "||",
    "(",
    ")",
    "{",
    "}",
}

SHELL_INTERPRETERS = {
    "bash",
    "dash",
    "fish",
    "ksh",
    "sh",
    "zsh",
}

SQL_CLIENTS = {
    "duckdb",
    "mariadb",
    "mysql",
    "psql",
    "sqlite",
    "sqlite3",
    "sqlcmd",
}

SQL_OPTION_FLAGS = {
    "-c",
    "--command",
    "-e",
    "--execute",
    "-q",
    "-Q",
    "/Q",
}

SQL_FILE_OPTION_FLAGS_BY_CLIENT = {
    "psql": {"-f", "--file"},
    "sqlcmd": {"-i", "--input", "--input-file"},
    "sqlite": {"-init"},
    "sqlite3": {"-init"},
}

SQL_STDIN_SOURCE_COMMANDS = {
    "cat",
    "type",
}

SQL_STDIN_TEXT_COMMANDS = {
    "echo",
    "printf",
}

MAX_SQL_FILE_BYTES = 1024 * 1024

SQL_KEYWORD_RE = re.compile(
    r"(?is)\b(drop\s+(?:table|database|schema)(?=\s|;|$)|truncate(?:\s+table)?(?=\s|;|$)|delete\s+from\b)"
)
SQL_STATEMENT_START_RE = re.compile(
    r"(?is)^\s*(?:drop\s+(?:table|database|schema)(?=\s|;|$)|truncate(?:\s+table)?(?=\s|;|$)|delete\s+from\b)"
)
DROP_OR_TRUNCATE_RE = re.compile(
    r"(?is)\b(?:drop\s+(?:table|database|schema)(?=\s|;|$)|truncate(?:\s+table)?(?=\s|;|$))"
)
DELETE_FROM_RE = re.compile(r"(?is)\bdelete\s+from\b")
WHERE_RE = re.compile(r"(?is)\bwhere\b")


@dataclass(frozen=True)
class Detection:
    rule: str
    reason: str
    evidence: str
    severity: str = "high"


def main() -> int:
    payload = read_json(sys.stdin.read())
    if payload is None:
        return 0

    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    if tool_name.lower() != "bash":
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    project_path = extract_project_path(payload)
    detection = detect_destructive_command(command, project_path)
    if detection is None:
        return 0

    log_blocked_attempt(command, project_path, detection)
    print(deny_response(detection))
    return 0


def read_json(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def detect_destructive_command(command: str, cwd: str | None = None, depth: int = 0) -> Detection | None:
    if depth > 3:
        return None

    tokens = shell_tokens(command)
    if not tokens:
        return fallback_text_detection(command)

    for embedded_command in embedded_shell_commands(tokens):
        detection = detect_destructive_command(embedded_command, cwd, depth + 1)
        if detection is not None:
            return detection

    for detector in (detect_rm_recursive_force, detect_git_force_push):
        detection = detector(command, tokens)
        if detection is not None:
            return detection

    detection = detect_destructive_sql(command, tokens, cwd)
    if detection is not None:
        return detection

    return None


def shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|(){}")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        return list(lexer)
    except ValueError:
        return []


def fallback_text_detection(command: str) -> Detection | None:
    lowered = command.lower()
    if re.search(r"(?:^|[\s;&|()])rm\s+-(?=[a-z-]*r)(?=[a-z-]*f)[a-z-]*\b", lowered):
        return Detection(
            "rm -rf",
            "Recursive forced deletion can remove large parts of the project or home directory.",
            "raw command matched rm with recursive and force flags",
            "critical",
        )
    if re.search(r"\bgit\s+push\b[^;&|\n]*?(?:--force(?:-with-lease)?\b|\s-f(?:\s|$)|\s\+\S+)", command, re.I):
        return Detection(
            "git push --force",
            "Force pushing can overwrite remote history.",
            "raw command matched git push with a force option or forced refspec",
            "high",
        )
    if SQL_KEYWORD_RE.search(strip_sql_comments_and_literals(command)):
        return classify_sql(command)
    return None


def embedded_shell_commands(tokens: list[str]) -> Iterable[str]:
    for index, token in enumerate(tokens):
        if base_name(token) not in SHELL_INTERPRETERS:
            continue

        for option_index in range(index + 1, len(tokens)):
            option = tokens[option_index]
            if option in COMMAND_SEPARATORS:
                break
            if not option.startswith("-"):
                break
            if "c" in option.lstrip("-"):
                command_index = option_index + 1
                if command_index < len(tokens):
                    yield tokens[command_index]
                break


def detect_rm_recursive_force(command: str, tokens: list[str]) -> Detection | None:
    del command
    for index, token in enumerate(tokens):
        if base_name(token) != "rm":
            continue

        recursive = False
        force = False
        operands: list[str] = []
        end_of_options = False

        for arg in command_args_after(tokens, index):
            if arg == "--":
                end_of_options = True
                continue
            if end_of_options:
                operands.append(arg)
                continue
            if arg.startswith("--"):
                recursive = recursive or arg in {"--recursive", "--dir"}
                force = force or arg == "--force"
                continue
            if arg.startswith("-") and arg != "-":
                flags = arg.lstrip("-")
                recursive = recursive or "r" in flags.lower() or "R" in flags
                force = force or "f" in flags
                continue
            operands.append(arg)

        if recursive and force:
            target = " ".join(operands) if operands else "(no explicit target)"
            return Detection(
                "rm -rf",
                "Recursive forced deletion can remove large parts of the project or home directory.",
                f"rm was invoked with recursive and force flags against {target}",
                "critical",
            )

    return None


def detect_git_force_push(command: str, tokens: list[str]) -> Detection | None:
    del command
    for index, token in enumerate(tokens):
        if base_name(token) != "git":
            continue

        args = list(command_args_after(tokens, index))
        subcommand_index = git_subcommand_index(args)
        if subcommand_index is None or args[subcommand_index] != "push":
            continue

        push_args = args[subcommand_index + 1 :]
        for arg in push_args:
            if arg in {"--force", "-f"} or arg.startswith("--force-with-lease"):
                return Detection(
                    "git push --force",
                    "Force pushing can overwrite remote history.",
                    f"git push used force option {arg}",
                    "high",
                )
            if arg.startswith("+") and len(arg) > 1:
                return Detection(
                    "git push forced refspec",
                    "A leading plus in a git push refspec forces the remote update.",
                    f"git push used forced refspec {arg}",
                    "high",
                )

    return None


def git_subcommand_index(args: list[str]) -> int | None:
    index = 0
    options_with_values = {
        "-C",
        "-c",
        "--git-dir",
        "--work-tree",
        "--namespace",
        "--config-env",
        "--exec-path",
    }

    while index < len(args):
        arg = args[index]
        if arg == "--":
            return index + 1 if index + 1 < len(args) else None
        if arg in options_with_values:
            index += 2
            continue
        if any(arg.startswith(option + "=") for option in options_with_values if option.startswith("--")):
            index += 1
            continue
        if arg.startswith("-"):
            index += 1
            continue
        return index

    return None


def detect_destructive_sql(command: str, tokens: list[str], cwd: str | None = None) -> Detection | None:
    direct_payload = direct_sql_payload(command)
    if direct_payload:
        detection = classify_sql(direct_payload)
        if detection is not None:
            return detection

    payloads = sql_payloads_from_clients(tokens)
    if has_sql_client(tokens):
        payloads.extend(sql_stdin_text_payloads_from_clients(tokens))
        if "<<" in command:
            payloads.append(command)

    for payload in payloads:
        detection = classify_sql(payload)
        if detection is not None:
            return detection

    for path, payload in sql_file_payloads_from_clients(tokens, cwd):
        detection = classify_sql(payload)
        if detection is not None:
            return Detection(
                detection.rule,
                detection.reason,
                f"{detection.evidence} in SQL input file {path}",
                detection.severity,
            )

    return None


def direct_sql_payload(command: str) -> str:
    normalized = strip_sql_comments_and_literals(command)
    for statement in split_sql_statements(normalized):
        if SQL_STATEMENT_START_RE.search(statement):
            return statement
    return ""


def sql_payloads_from_clients(tokens: list[str]) -> list[str]:
    payloads: list[str] = []
    for index, token in enumerate(tokens):
        if base_name(token) not in SQL_CLIENTS:
            continue

        args = list(command_args_after(tokens, index))
        for arg_index, arg in enumerate(args):
            normalized_arg = arg.lower()
            if normalized_arg in {flag.lower() for flag in SQL_OPTION_FLAGS} and arg_index + 1 < len(args):
                payloads.append(args[arg_index + 1])
            elif any(arg.lower().startswith(flag.lower() + "=") for flag in SQL_OPTION_FLAGS if flag.startswith("--")):
                payloads.append(arg.split("=", 1)[1])
            elif base_name(token) in {"sqlite", "sqlite3", "duckdb"} and looks_like_sql(arg):
                payloads.append(arg)

    return payloads


def sql_stdin_text_payloads_from_clients(tokens: list[str]) -> list[str]:
    payloads: list[str] = []
    for index, token in enumerate(tokens):
        if base_name(token) in SQL_CLIENTS:
            payloads.extend(piped_text_payloads(tokens, index))
    return payloads


def piped_text_payloads(tokens: list[str], sql_client_index: int) -> Iterable[str]:
    source_command = piped_source_command(tokens, sql_client_index)
    if not source_command or base_name(source_command[0]) not in SQL_STDIN_TEXT_COMMANDS:
        return

    args = [
        arg
        for arg in source_command[1:]
        if arg != "--" and not (base_name(source_command[0]) == "echo" and arg.startswith("-"))
    ]
    if args:
        yield " ".join(args)


def sql_file_payloads_from_clients(tokens: list[str], cwd: str | None = None) -> list[tuple[str, str]]:
    payloads: list[tuple[str, str]] = []
    seen: set[Path] = set()

    for index, token in enumerate(tokens):
        if base_name(token) not in SQL_CLIENTS:
            continue

        for candidate in sql_file_candidates(tokens, index):
            resolved = resolve_sql_file(candidate, cwd)
            if resolved is None or resolved in seen:
                continue
            seen.add(resolved)
            content = read_sql_file(resolved)
            if content is not None:
                payloads.append((str(resolved), content))

    return payloads


def sql_file_candidates(tokens: list[str], sql_client_index: int) -> Iterable[str]:
    client = base_name(tokens[sql_client_index])
    file_flags = SQL_FILE_OPTION_FLAGS_BY_CLIENT.get(client, set())
    args = list(command_args_after(tokens, sql_client_index))
    for arg_index, arg in enumerate(args):
        lowered = arg.lower()
        if lowered in file_flags and arg_index + 1 < len(args):
            yield args[arg_index + 1]
        elif any(
            lowered.startswith(flag + "=")
            for flag in file_flags
            if flag.startswith("--")
        ):
            yield arg.split("=", 1)[1]
        elif "-f" in file_flags and lowered.startswith("-f") and len(arg) > 2:
            yield arg[2:]
        elif "-i" in file_flags and lowered.startswith("-i") and len(arg) > 2:
            yield arg[2:]
        elif lowered.startswith("<") and len(arg) > 1 and not lowered.startswith("<<"):
            yield arg[1:]
        elif arg == "<" and arg_index + 1 < len(args):
            yield args[arg_index + 1]

    yield from piped_file_candidates(tokens, sql_client_index)


def piped_file_candidates(tokens: list[str], sql_client_index: int) -> Iterable[str]:
    source_command = piped_source_command(tokens, sql_client_index)
    if not source_command or base_name(source_command[0]) not in SQL_STDIN_SOURCE_COMMANDS:
        return

    for arg in source_command[1:]:
        if arg == "--":
            continue
        if arg.startswith("-"):
            continue
        yield arg


def piped_source_command(tokens: list[str], sql_client_index: int) -> list[str]:
    pipe_index = sql_client_index - 1
    while pipe_index >= 0 and tokens[pipe_index] not in {"|", "|&"}:
        if tokens[pipe_index] in COMMAND_SEPARATORS:
            return []
        pipe_index -= 1
    if pipe_index < 1:
        return []

    source_start = pipe_index - 1
    while source_start > 0 and tokens[source_start - 1] not in COMMAND_SEPARATORS:
        source_start -= 1
    return tokens[source_start:pipe_index]


def resolve_sql_file(candidate: str, cwd: str | None = None) -> Path | None:
    if not candidate or candidate in {"-", "/dev/stdin"}:
        return None
    if any(char in candidate for char in "\x00$`*?[]{}"):
        return None

    path = Path(os.path.expanduser(candidate))
    if not path.is_absolute():
        path = Path(cwd or os.getcwd()).expanduser() / path

    try:
        resolved = path.resolve(strict=False)
    except OSError:
        return None
    return resolved


def read_sql_file(path: Path) -> str | None:
    try:
        file_stat = path.stat()
        if not path.is_file() or file_stat.st_size > MAX_SQL_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def has_sql_client(tokens: list[str]) -> bool:
    return any(base_name(token) in SQL_CLIENTS for token in tokens)


def classify_sql(sql: str) -> Detection | None:
    normalized = strip_sql_comments_and_literals(sql)
    drop_or_truncate = DROP_OR_TRUNCATE_RE.search(normalized)
    if drop_or_truncate:
        matched_keyword = " ".join(drop_or_truncate.group(0).upper().split())
        rule = "TRUNCATE" if matched_keyword.startswith("TRUNCATE") else matched_keyword
        return Detection(
            rule,
            f"{rule} can irreversibly remove database objects or table contents.",
            drop_or_truncate.group(0),
            "critical",
        )

    for statement in split_sql_statements(normalized):
        delete_match = DELETE_FROM_RE.search(statement)
        if not delete_match:
            continue
        if not WHERE_RE.search(statement[delete_match.end() :]):
            return Detection(
                "DELETE FROM without WHERE",
                "DELETE FROM without a WHERE clause can delete every row in the table.",
                statement.strip(),
                "critical",
            )

    return None


def strip_sql_comments_and_literals(sql: str) -> str:
    result: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if quote:
            if char == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            result.append(" ")
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            result.append(" ")
            index += 1
            continue

        if char == "-" and next_char == "-":
            while index < len(sql) and sql[index] not in "\r\n":
                result.append(" ")
                index += 1
            continue

        if char == "/" and next_char == "*":
            result.extend("  ")
            index += 2
            while index + 1 < len(sql) and not (sql[index] == "*" and sql[index + 1] == "/"):
                result.append(" ")
                index += 1
            if index + 1 < len(sql):
                result.extend("  ")
                index += 2
            continue

        result.append(char)
        index += 1

    return "".join(result)


def split_sql_statements(sql: str) -> list[str]:
    return [statement for statement in sql.split(";") if statement.strip()]


def looks_like_sql(value: str) -> bool:
    return bool(SQL_KEYWORD_RE.search(value))


def command_args_after(tokens: list[str], command_index: int) -> Iterable[str]:
    for token in tokens[command_index + 1 :]:
        if token in COMMAND_SEPARATORS:
            break
        yield token


def base_name(token: str) -> str:
    normalized = token.replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", 1)[-1].lower()


def extract_project_path(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cwd", "workdir", "project_path", "project_dir", "workspace"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value

    for key in ("cwd", "workdir", "project_path", "project_dir", "workspace"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    transcript_path = payload.get("transcript_path")
    if isinstance(transcript_path, str) and transcript_path:
        return parent_path_string(transcript_path)

    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def parent_path_string(value: str) -> str:
    expanded = os.path.expanduser(value).rstrip("/\\")
    separator_index = max(expanded.rfind("/"), expanded.rfind("\\"))
    if separator_index > 0:
        return expanded[:separator_index]
    if separator_index == 0:
        return expanded[:1]
    return str(Path(expanded).parent)


def hook_dir() -> Path:
    override = os.environ.get("CLAUDE_HOOKS_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks"


def log_blocked_attempt(command: str, project_path: str, detection: Detection) -> None:
    log_path = hook_dir() / "blocked.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": detection.severity,
            "rule": detection.rule,
            "pattern": detection.rule,
            "reason": detection.reason,
            "evidence": detection.evidence,
            "command": command,
            "project_path": project_path,
        }
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        # Blocking should not depend on logging success.
        pass


def deny_response(detection: Detection) -> str:
    message = (
        f"Blocked potentially destructive Bash command ({detection.rule}). "
        f"{detection.reason} Evidence: {detection.evidence}. "
        "Use a narrower, reversible, or explicitly reviewed command instead."
    )
    response = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    return json.dumps(response)


if __name__ == "__main__":
    raise SystemExit(main())
