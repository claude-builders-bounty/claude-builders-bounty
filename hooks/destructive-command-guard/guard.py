#!/usr/bin/env python3
"""Best-effort Claude Code PreToolUse guard for destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys
from typing import NamedTuple

BACKTICK = chr(96)
SQL_CLIENTS = {"mysql", "mariadb", "psql", "sqlite3", "sqlcmd"}
SHELLS = {"bash", "dash", "sh", "zsh"}
ESCAPED_SEMICOLON = "\ue000"
SHELL_PUNCTUATION = ";&|()<>\n"
MAX_COMMAND_BYTES = 1_000_000
MAX_NESTING = 16


class HereDocument(NamedTuple):
    body: str
    quoted: bool
    target: str


def _heredoc_openers(line: str) -> list[tuple[str, bool, bool]]:
    """Return simple <<WORD redirections outside shell quotes."""
    found: list[tuple[str, bool, bool]] = []
    quote: str | None = None
    escaped = False
    i = 0
    while i < len(line):
        char = line[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if quote == "'":
            if char == "'":
                quote = None
            i += 1
            continue
        if quote == '"':
            if char == "\\":
                escaped = True
            elif char == '"':
                quote = None
            i += 1
            continue
        if char == "\\":
            escaped = True
            i += 1
            continue
        if char in {"'", '"'}:
            quote = char
            i += 1
            continue
        if char == "#" and (
            i == 0 or line[i - 1].isspace() or line[i - 1] in ";&|()<>"
        ):
            break
        if line.startswith("<<", i) and not line.startswith("<<<", i):
            i += 2
            strip_tabs = i < len(line) and line[i] == "-"
            if strip_tabs:
                i += 1
            while i < len(line) and line[i] in " \t":
                i += 1
            delimiter = ""
            quoted = False
            if i < len(line) and line[i] in {"'", '"'}:
                delimiter_quote = line[i]
                quoted = True
                i += 1
                while i < len(line) and line[i] != delimiter_quote:
                    if line[i] == "\\" and delimiter_quote == '"' and i + 1 < len(line):
                        i += 1
                    delimiter += line[i]
                    i += 1
                if i < len(line):
                    i += 1
            else:
                while i < len(line) and line[i] not in " \t\r\n;&|<>":
                    if line[i] == "\\" and i + 1 < len(line):
                        i += 1
                    delimiter += line[i]
                    i += 1
            if delimiter:
                found.append((delimiter, strip_tabs, quoted))
            continue
        i += 1
    return found


def _normalize_shell_boundaries(command: str) -> str:
    """Preserve command newlines while removing shell comments before shlex tokenizing."""
    output: list[str] = []
    quote: str | None = None
    in_comment = False
    index = 0
    while index < len(command):
        char = command[index]
        if in_comment:
            if char == "\n":
                output.append(";")
                in_comment = False
            index += 1
            continue

        if quote == "'":
            output.append(char)
            if char == "'":
                quote = None
            index += 1
            continue

        if quote == '"':
            if char == "\\" and index + 1 < len(command):
                if command[index + 1] != "\n":
                    output.extend((char, command[index + 1]))
                index += 2
                continue
            output.append(char)
            if char == '"':
                quote = None
            index += 1
            continue

        if char == "\\" and index + 1 < len(command):
            if command[index + 1] == ";":
                output.append(ESCAPED_SEMICOLON)
                index += 2
                continue
            if command[index + 1] != "\n":
                output.extend((char, command[index + 1]))
            index += 2
            continue
        if char in {"'", '"'}:
            quote = char
            output.append(char)
        elif char == "#" and (
            index == 0
            or command[index - 1].isspace()
            or command[index - 1] in ";&|()<>"
        ):
            in_comment = True
        elif char == "\n":
            output.append(";")
        else:
            output.append(char)
        index += 1
    return "".join(output)


def _tokens(command: str) -> list[str]:
    lexer = shlex.shlex(
        _normalize_shell_boundaries(command),
        posix=True,
        punctuation_chars=SHELL_PUNCTUATION,
    )
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    return list(lexer)


def _segments(command: str) -> list[list[str]]:
    return _segments_and_operators(command)[0]


def _segments_and_operators(command: str) -> tuple[list[list[str]], list[str]]:
    segments: list[list[str]] = []
    operators: list[str] = []
    current: list[str] = []
    try:
        words = _tokens(command)
    except ValueError as exc:
        raise ValueError(
            "shell quoting is incomplete; command cannot be inspected"
        ) from exc
    for word in words:
        if word == "<<<":
            current.append(word)
            continue
        if word and all(char in SHELL_PUNCTUATION for char in word):
            if current:
                segments.append(current)
                current = []
                operators.append(word)
        else:
            current.append(word)
    if current:
        segments.append(current)
    if len(operators) >= len(segments):
        operators = operators[: len(segments) - 1]
    return segments, operators


def _target_for_heredoc(line: str) -> str:
    """Classify simple here-doc input by the command receiving it."""
    before = line
    for marker in ("<<-", "<<"):
        before = before.split(marker, 1)[0]
    try:
        segments = _segments(before)
    except ValueError:
        return "data"
    names = [Path(token).name for segment in segments for token in segment]
    if any(name in SQL_CLIENTS for name in names):
        return "sql"
    if any(name in SHELLS for name in names):
        return "shell"
    return "data"


def _mask_heredocs(command: str) -> tuple[str, list[HereDocument]]:
    lines = command.splitlines(keepends=True)
    masked = list(lines)
    bodies: list[HereDocument] = []
    index = 0
    while index < len(lines):
        openers = _heredoc_openers(lines[index])
        if not openers:
            index += 1
            continue
        target = _target_for_heredoc(lines[index])
        cursor = index + 1
        for delimiter, strip_tabs, quoted in openers:
            body_lines: list[str] = []
            found_end = False
            while cursor < len(lines):
                candidate = lines[cursor].rstrip("\r\n")
                compare = candidate.lstrip("\t") if strip_tabs else candidate
                masked[cursor] = "\n" if lines[cursor].endswith("\n") else ""
                cursor += 1
                if compare == delimiter:
                    found_end = True
                    break
                body_lines.append(lines[cursor - 1])
            bodies.append(HereDocument("".join(body_lines), quoted, target))
            if not found_end:
                cursor = len(lines)
                break
        index = max(cursor, index + 1)
    return "".join(masked), bodies


def _matching_paren(command: str, open_index: int) -> int | None:
    """Find the close paren for a shell command/process substitution."""
    depth = 1
    quote: str | None = None
    escaped = False
    i = open_index + 1
    while i < len(command):
        char = command[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if quote == "'":
            if char == "'":
                quote = None
            i += 1
            continue
        if quote == '"':
            if char == "\\":
                escaped = True
            elif char == '"':
                quote = None
            elif command.startswith("$(", i):
                depth += 1
                i += 2
                continue
            elif char == BACKTICK:
                end = _matching_backtick(command, i)
                if end is not None:
                    i = end + 1
                    continue
            i += 1
            continue
        if char == "\\":
            escaped = True
        elif char == "'":
            quote = "'"
        elif char == '"':
            quote = '"'
        elif char == BACKTICK:
            end = _matching_backtick(command, i)
            if end is not None:
                i = end + 1
                continue
        elif command.startswith("$(", i):
            depth += 1
            i += 2
            continue
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _matching_backtick(command: str, open_index: int) -> int | None:
    i = open_index + 1
    while i < len(command):
        if command[i] == "\\":
            i += 2
            continue
        if command[i] == BACKTICK:
            return i
        i += 1
    return None


def _nested_shell_commands(command: str) -> list[str]:
    """Extract command/process substitutions without interpreting quoted text."""
    nested: list[str] = []
    quote: str | None = None
    escaped = False
    token_start = True
    i = 0
    while i < len(command):
        char = command[i]
        if escaped:
            escaped = False
            token_start = False
            i += 1
            continue
        if quote == "'":
            if char == "'":
                quote = None
            i += 1
            continue
        if quote == '"':
            if char == "\\":
                escaped = True
                i += 1
                continue
            if char == '"':
                quote = None
                i += 1
                continue
        else:
            if char == "\\":
                escaped = True
                i += 1
                continue
            if char == "'":
                quote = "'"
                i += 1
                continue
            if char == '"':
                quote = '"'
                i += 1
                continue
            if char == "#" and token_start:
                newline = command.find("\n", i)
                if newline < 0:
                    break
                i = newline + 1
                token_start = True
                continue
        if command.startswith("$(", i) or (
            quote is None
            and i + 1 < len(command)
            and command[i] in "<>"
            and command[i + 1] == "("
        ):
            open_index = i + 1
            close_index = _matching_paren(command, open_index)
            if close_index is not None:
                nested.append(command[open_index + 1 : close_index])
                i = close_index + 1
                token_start = False
                continue
        if char == BACKTICK and quote != "'":
            close_index = _matching_backtick(command, i)
            if close_index is not None:
                nested.append(command[i + 1 : close_index])
                i = close_index + 1
                token_start = False
                continue
        token_start = char.isspace() or char in ";&|()<>"
        i += 1
    return nested


def _mask_escaped_command_substitutions(command: str) -> str:
    """Keep escaped dollar-parenthesis text out of the shell token stream."""
    output: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(command):
        char = command[i]
        if quote == "'":
            output.append(char)
            if char == "'":
                quote = None
            i += 1
            continue
        if quote == '"':
            if char == "\\" and i + 1 < len(command):
                if command.startswith("$(", i + 1):
                    close_index = _matching_paren(command, i + 2)
                    if close_index is not None:
                        output.append("LITERAL_SUBSTITUTION")
                        i = close_index + 1
                        continue
                output.append(command[i : i + 2])
                i += 2
                continue
            output.append(char)
            if char == '"':
                quote = None
            i += 1
            continue
        if char == "\\" and i + 1 < len(command):
            if command.startswith("$(", i + 1):
                close_index = _matching_paren(command, i + 2)
                if close_index is not None:
                    output.append("LITERAL_SUBSTITUTION")
                    i = close_index + 1
                    continue
            output.append(command[i : i + 2])
            i += 2
            continue
        if char == "'":
            quote = "'"
        elif char == '"':
            quote = '"'
        output.append(char)
        i += 1
    return "".join(output)


def _sql_statements(text: str) -> list[list[tuple[str, int]]]:
    """Tokenize basic SQL while ignoring comments and quoted values."""
    statements: list[list[tuple[str, int]]] = []
    current: list[tuple[str, int]] = []
    depth = 0
    i = 0
    while i < len(text):
        if text.startswith("--", i):
            newline = text.find("\n", i + 2)
            i = len(text) if newline < 0 else newline + 1
            continue
        if text[i] == "#":
            newline = text.find("\n", i + 1)
            i = len(text) if newline < 0 else newline + 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end < 0 else end + 2
            continue
        dollar_quote = re.match(r"\$[A-Za-z_0-9]*\$", text[i:])
        if dollar_quote:
            delimiter = dollar_quote.group(0)
            end = text.find(delimiter, i + len(delimiter))
            if end >= 0:
                i = end + len(delimiter)
                continue
        char = text[i]
        if char in {"'", '"', BACKTICK}:
            quote = char
            i += 1
            while i < len(text):
                if text[i] == quote:
                    if i + 1 < len(text) and text[i + 1] == quote:
                        i += 2
                        continue
                    i += 1
                    break
                if text[i] == "\\" and quote != "'":
                    i += 1
                i += 1
            continue
        if char == "[":
            end = text.find("]", i + 1)
            i = len(text) if end < 0 else end + 1
            continue
        if char == ";":
            statements.append(current)
            current = []
            depth = 0
            i += 1
            continue
        if char == "(":
            depth += 1
            i += 1
            continue
        if char == ")":
            depth = max(0, depth - 1)
            i += 1
            continue
        match = re.match(r"[A-Za-z_][A-Za-z_0-9$]*", text[i:])
        if match:
            current.append((match.group(0).upper(), depth))
            i += len(match.group(0))
            continue
        i += 1
    statements.append(current)
    return statements


def _sql_reason(text: str) -> str | None:
    for statement in _sql_statements(text):
        top_level = [word for word, level in statement if level == 0]
        for index, word in enumerate(top_level):
            if word == "DROP" and top_level[index + 1 : index + 2] == ["TABLE"]:
                return "DROP TABLE removes a database table."
            if word == "TRUNCATE":
                return "TRUNCATE removes all rows from a table."
            if (
                word == "DELETE"
                and top_level[index + 1 : index + 2] == ["FROM"]
                and "WHERE" not in top_level[index + 2 :]
            ):
                return "DELETE FROM has no top-level WHERE clause."
    return None


def _rm_reason(args: list[str]) -> str | None:
    recursive = False
    force = False
    for arg in args:
        if arg == "--":
            break
        if arg == "--recursive":
            recursive = True
        elif arg == "--force":
            force = True
        elif arg.startswith("--"):
            continue
        elif arg.startswith("-"):
            recursive |= "r" in arg[1:] or "R" in arg[1:]
            force |= "f" in arg[1:]
    if recursive and force:
        return "rm combines recursive deletion with force."
    return None


def _git_push_reason(args: list[str]) -> str | None:
    rest = list(args)
    option_values = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
    while rest and rest[0].startswith("-"):
        option = rest.pop(0)
        if option in option_values and rest:
            rest.pop(0)
    if not rest or rest[0] != "push":
        return None
    options_ended = False
    for arg in rest[1:]:
        if arg == "--" and not options_ended:
            options_ended = True
            continue
        forced_option = not options_ended and (
            arg in {"--force", "--force-with-lease", "--force-if-includes"}
            or arg.startswith("--force-with-lease=")
            or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:])
        )
        # The option terminator does not remove the force meaning of a + refspec.
        if forced_option or arg.startswith("+"):
            return "git push requests a forced remote update."
    return None


def _unwrap_execution_prefix(argv: list[str]) -> list[str]:
    """Unwrap common command launchers without treating arbitrary arguments as code."""
    remaining = list(argv)
    while remaining:
        while remaining and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", remaining[0]):
            remaining = remaining[1:]
        if not remaining:
            return []
        executable = Path(remaining[0]).name
        if executable == "env":
            args = remaining[1:]
            index = 0
            while index < len(args):
                arg = args[index]
                if arg == "--":
                    index += 1
                    break
                if arg in {"-u", "--unset", "-C", "--chdir"}:
                    index += 2
                    continue
                if (
                    arg in {"-S", "--split-string"}
                    or arg.startswith("--split-string=")
                    or (arg.startswith("-S") and len(arg) > 2)
                ):
                    if arg in {"-S", "--split-string"}:
                        if index + 1 >= len(args):
                            return []
                        source, consumed = args[index + 1], 2
                    elif arg.startswith("--split-string="):
                        source, consumed = arg.partition("=")[2], 1
                    else:
                        source, consumed = arg[2:], 1
                    try:
                        split = shlex.split(source, posix=True)
                    except ValueError:
                        return []
                    return _unwrap_execution_prefix(split + args[index + consumed :])
                if arg.startswith(("--unset=", "--chdir=")) or (
                    arg.startswith("-u") and len(arg) > 2
                ):
                    index += 1
                    continue
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", arg):
                    index += 1
                    continue
                if arg.startswith("-"):
                    index += 1
                    continue
                break
            remaining = args[index:]
            continue

        if executable == "sudo":
            args = remaining[1:]
            index = 0
            value_options = {
                "-C",
                "-D",
                "-g",
                "-h",
                "-p",
                "-r",
                "-t",
                "-u",
                "--close-from",
                "--chdir",
                "--group",
                "--host",
                "--other-user",
                "--prompt",
                "--role",
                "--type",
                "--user",
            }
            while index < len(args):
                arg = args[index]
                if arg == "--":
                    index += 1
                    break
                if arg in value_options:
                    index += 2
                elif arg.startswith("--") and "=" in arg:
                    index += 1
                elif arg.startswith("-"):
                    index += 1
                else:
                    break
            remaining = args[index:]
            continue

        if executable in {"command", "exec"}:
            args = remaining[1:]
            index = 0
            while index < len(args):
                arg = args[index]
                if arg == "--":
                    index += 1
                    break
                if executable == "exec" and arg == "-a":
                    index += 2
                elif arg.startswith("-"):
                    index += 1
                else:
                    break
            remaining = args[index:]
            continue

        if executable in {"nohup", "busybox"}:
            remaining = remaining[1:]
            continue

        if executable == "time":
            args = remaining[1:]
            index = 0
            while index < len(args) and args[index].startswith("-"):
                arg = args[index]
                if arg in {"-f", "--format", "-o", "--output"}:
                    index += 2
                else:
                    index += 1
            remaining = args[index:]
            continue

        if executable == "timeout":
            args = remaining[1:]
            index = 0
            while index < len(args) and args[index].startswith("-"):
                arg = args[index]
                if arg in {"-k", "--kill-after", "-s", "--signal"}:
                    index += 2
                elif arg.startswith("--") and "=" in arg:
                    index += 1
                else:
                    index += 1
            if index < len(args):
                index += 1  # duration
            remaining = args[index:]
            continue

        if executable == "nice":
            args = remaining[1:]
            index = 0
            while index < len(args) and args[index].startswith("-"):
                arg = args[index]
                if arg in {"-n", "--adjustment"}:
                    index += 2
                elif arg.startswith("--adjustment=") or (
                    arg.startswith("-n") and len(arg) > 2
                ):
                    index += 1
                elif re.fullmatch(r"-\d+", arg):
                    index += 1
                else:
                    break
            remaining = args[index:]
            continue

        if executable == "stdbuf":
            args = remaining[1:]
            index = 0
            while index < len(args) and args[index].startswith("-"):
                arg = args[index]
                if arg in {"-i", "-o", "-e", "--input", "--output", "--error"}:
                    index += 2
                elif arg.startswith("--") and "=" in arg:
                    index += 1
                else:
                    index += 1
            remaining = args[index:]
            continue

        if executable == "xargs":
            args = remaining[1:]
            index = 0
            value_options = {
                "-a",
                "-d",
                "-E",
                "-I",
                "-L",
                "-n",
                "-P",
                "-s",
                "--arg-file",
                "--delimiter",
                "--eof",
                "--max-args",
                "--max-chars",
                "--max-lines",
                "--max-procs",
                "--replace",
            }
            while index < len(args):
                arg = args[index]
                if arg == "--":
                    index += 1
                    break
                if arg in value_options:
                    index += 2
                elif arg.startswith("--") and "=" in arg:
                    index += 1
                elif arg.startswith("-"):
                    index += 1
                else:
                    break
            remaining = args[index:]
            continue

        return remaining
    return []


def _find_exec_commands(argv: list[str]) -> list[list[str]]:
    """Extract commands that find passes to -exec/-execdir/-ok actions."""
    if not argv or Path(argv[0]).name != "find":
        return []
    commands: list[list[str]] = []
    index = 1
    actions = {"-exec", "-execdir", "-ok", "-okdir"}
    while index < len(argv):
        if argv[index] not in actions:
            index += 1
            continue
        start = index + 1
        end = start
        while end < len(argv) and argv[end] not in {
            ";",
            "+",
            ESCAPED_SEMICOLON,
        }:
            end += 1
        if end > start:
            commands.append(argv[start:end])
        index = end + 1
    return commands


def _here_string_sources(args: list[str]) -> list[str]:
    sources: list[str] = []
    index = 0
    while index < len(args):
        if args[index] == "<<<" and index + 1 < len(args):
            sources.append(args[index + 1])
            index += 2
        else:
            index += 1
    return sources


def _shell_reads_stdin_as_script(args: list[str]) -> bool:
    """Return whether a shell invocation uses stdin as its script source."""
    without_here_strings: list[str] = []
    index = 0
    while index < len(args):
        if args[index] == "<<<":
            index += 2
        else:
            without_here_strings.append(args[index])
            index += 1

    index = 0
    while index < len(without_here_strings):
        arg = without_here_strings[index]
        if arg in {"-c", "--command"} or (
            arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]
        ):
            return False
        if arg == "-s":
            index += 1
            continue
        if arg in {"--rcfile", "--init-file", "-o", "+o", "-O", "+O"}:
            index += 2
            continue
        if arg == "--":
            if index + 1 < len(without_here_strings):
                return without_here_strings[index + 1] in {"-", "/dev/stdin"}
            return True
        if arg in {"-", "/dev/stdin"}:
            return True
        if arg.startswith("-"):
            index += 1
            continue
        return False
    return True


def _inspect_command_argv(argv: list[str], depth: int) -> str | None:
    command = _unwrap_execution_prefix(argv)
    if not command:
        return None
    first = Path(command[0]).name
    if first == "rm":
        reason = _rm_reason(command[1:])
        if reason:
            return reason
    elif first == "git":
        reason = _git_push_reason(command[1:])
        if reason:
            return reason
    elif first in SQL_CLIENTS:
        reason = _sql_from_segments([command], [])
        if reason:
            return reason
        if Path(argv[0]).name != "xargs":
            for index, arg in enumerate(command[:-1]):
                if arg == "<<<":
                    reason = _sql_reason(command[index + 1])
                    if reason:
                        return reason
    if first in SHELLS:
        args = command[1:]
        if _shell_reads_stdin_as_script(args):
            for source in _here_string_sources(args):
                reason = inspect(source, depth + 1)
                if reason:
                    return reason
        for index, arg in enumerate(args):
            if arg == "-c" or (
                arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]
            ):
                if index + 1 < len(args):
                    return inspect(args[index + 1], depth + 1)
                break
    elif first == "eval":
        return inspect(" ".join(command[1:]), depth + 1)
    return None


def _sql_from_segments(segments: list[list[str]], operators: list[str]) -> str | None:
    for segment in segments:
        if not segment:
            continue
        first = Path(segment[0]).name
        if first in SQL_CLIENTS:
            collect = False
            query_parts: list[str] = []
            for arg in segment[1:]:
                if arg in {
                    "-c",
                    "--command",
                    "-e",
                    "--execute",
                    "--query",
                    "-Q",
                    "-q",
                    "-cmd",
                }:
                    collect = True
                    continue
                if arg.startswith(("--command=", "--execute=", "--query=")):
                    query_parts.append(arg.split("=", 1)[1])
                    continue
                if arg.startswith("-c") and len(arg) > 2:
                    query_parts.append(arg[2:])
                    continue
                if collect:
                    query_parts.append(arg)
            if query_parts:
                reason = _sql_reason(" ".join(query_parts))
                if reason:
                    return reason
            if first == "sqlite3" and len(segment) >= 3:
                reason = _sql_reason(segment[-1])
                if reason:
                    return reason
        elif first.upper() in {"DELETE", "DROP", "TRUNCATE"}:
            reason = _sql_reason(" ".join(segment))
            if reason:
                return reason

    # Scan text producers only when their output flows directly to a SQL client.
    for index, segment in enumerate(segments[:-1]):
        if (
            len(segment) > 1
            and Path(segment[0]).name in {"echo", "printf"}
            and index < len(operators)
            and "|" in operators[index]
            and Path(segments[index + 1][0]).name in SQL_CLIENTS
        ):
            reason = _sql_reason(" ".join(segment[1:]))
            if reason:
                return reason
    return None


def inspect(command: str, depth: int = 0) -> str | None:
    """Return a denial reason if the command contains a covered destructive action."""
    if depth > MAX_NESTING:
        return "command nesting is too deep to inspect safely."
    if len(command.encode("utf-8", errors="replace")) > MAX_COMMAND_BYTES:
        return "command is too large to inspect safely."

    command, heredocs = _mask_heredocs(command)
    for document in heredocs:
        if document.target == "sql":
            reason = _sql_reason(document.body)
            if reason:
                return reason
        elif document.target == "shell":
            reason = inspect(document.body, depth + 1)
            if reason:
                return reason
        elif not document.quoted:
            for nested in _nested_shell_commands(document.body):
                reason = inspect(nested, depth + 1)
                if reason:
                    return reason

    command = _mask_escaped_command_substitutions(command)
    for nested in _nested_shell_commands(command):
        reason = inspect(nested, depth + 1)
        if reason:
            return reason

    try:
        segments, operators = _segments_and_operators(command)
    except ValueError as exc:
        return str(exc) + "."

    for segment in segments:
        if not segment:
            continue
        commands = [segment, *_find_exec_commands(segment)]
        for argv in commands:
            reason = _inspect_command_argv(argv, depth)
            if reason:
                return reason

    return _sql_from_segments(segments, operators)


def _log_block(command: str, cwd: str) -> str | None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_path = log_dir / "blocked.log"
    try:
        log_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(log_path, flags, stat.S_IRUSR | stat.S_IWUSR)
        try:
            record = {
                "timestamp": dt.datetime.now(dt.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "command": command,
                "project_path": cwd,
            }
            payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
            if hasattr(os, "fchmod"):
                os.fchmod(descriptor, stat.S_IRUSR | stat.S_IWUSR)
            offset = 0
            while offset < len(payload):
                written = os.write(descriptor, payload[offset:])
                if written <= 0:
                    raise OSError("short write")
                offset += written
        finally:
            os.close(descriptor)
        return None
    except OSError as exc:
        return (
            " The command was denied, but the audit log could not be written"
            f" ({exc.__class__.__name__})."
        )


def _deny(reason: str, command: str, cwd: str) -> None:
    log_failure = _log_block(command, cwd)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Destructive command blocked: "
            + reason
            + (log_failure or ""),
        }
    }
    print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("Invalid PreToolUse JSON; Bash call denied.", file=sys.stderr)
        return 2
    if not isinstance(event, dict) or event.get("tool_name") != "Bash":
        return 0
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict) or not isinstance(
        tool_input.get("command"), str
    ):
        _deny(
            "Bash command input is missing or malformed.", "", str(event.get("cwd", ""))
        )
        return 0

    command = tool_input["command"]
    cwd = event.get("cwd", "")
    if not isinstance(cwd, str):
        cwd = ""
    reason = inspect(command)
    if reason:
        _deny(reason, command, cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
