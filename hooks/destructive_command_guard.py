#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell commands.

The hook is deliberately dependency-free. Claude Code sends a JSON object on
stdin for every matching Bash tool call; a deny decision is returned on stdout
when a dangerous command is found. All other calls exit quietly with status 0.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import re
import shlex
import sys
from typing import Any, Iterable, TextIO


_SHELL_SEPARATORS = {";", "&&", "||", "|", "&", "\n"}
_SQL_CLIENTS = {
    "duckdb",
    "mariadb",
    "mysql",
    "psql",
    "sqlite",
    "sqlite3",
    "sqlcmd",
}
_SHELL_WRAPPERS = {"bash", "dash", "fish", "ksh", "sh", "zsh"}
_MAX_SHELL_NESTING = 32
_SQL_DROP_RE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
_SQL_TRUNCATE_RE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)
_SQL_DELETE_RE = re.compile(
    r"\bDELETE(?:\s+|/\*.*?\*/)+FROM\b",
    re.IGNORECASE | re.DOTALL,
)
_SQL_DOLLAR_QUOTE_RE = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$")
_GIT_REMOTE_PUSH_CONFIG_RE = re.compile(r"^remote\.[^.]+\.push$", re.IGNORECASE)
_GIT_REMOTE_MIRROR_CONFIG_RE = re.compile(r"^remote\.[^.]+\.mirror$", re.IGNORECASE)
_GIT_TRUE_VALUES = {"1", "on", "true", "yes"}
_LOG_VALUE = r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s;&|,]+)'''
_SECRET_NAME = (
    r"[A-Za-z0-9_-]*(?:token|secret|password|passwd|api[-_]?key|"
    r"access[-_]?key|private[-_]?key|authorization|credential)[A-Za-z0-9_-]*"
)
_SECRET_FLAG_EQUALS_RE = re.compile(
    rf"(?i)(--{_SECRET_NAME}\s*=\s*)({_LOG_VALUE})"
)
_SECRET_FLAG_ARGUMENT_RE = re.compile(
    rf"(?i)(--{_SECRET_NAME}\s+)({_LOG_VALUE})"
)
_SECRET_ASSIGNMENT_RE = re.compile(
    rf"(?i)((?:[\"']?{_SECRET_NAME}[\"']?)\s*[:=]\s*)({_LOG_VALUE})"
)
_BEARER_VALUE_RE = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/-]+=*")
_URL_CREDENTIALS_RE = re.compile(r"(?i)(https?://)[^/@\s:]+:[^/@\s]+@")
_COMMON_TOKEN_RE = re.compile(
    r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16})\b"
)


def _redacted_value(match: re.Match[str]) -> str:
    """Keep the original quoting while replacing a matched secret value."""
    value = match.group(2)
    quote = (
        value[0]
        if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]
        else ""
    )
    return f"{match.group(1)}{quote}[REDACTED]{quote}"


def _redact_command_for_log(command: str) -> str:
    """Best-effort redact credentials before persisting an attempted command."""
    sanitized = _SECRET_FLAG_EQUALS_RE.sub(_redacted_value, command)
    sanitized = _SECRET_FLAG_ARGUMENT_RE.sub(_redacted_value, sanitized)
    sanitized = _SECRET_ASSIGNMENT_RE.sub(_redacted_value, sanitized)
    sanitized = _BEARER_VALUE_RE.sub(r"\1[REDACTED]", sanitized)
    sanitized = _URL_CREDENTIALS_RE.sub(r"\1[REDACTED]@", sanitized)
    sanitized = _COMMON_TOKEN_RE.sub("[REDACTED]", sanitized)
    return sanitized[:4000] + ("…[TRUNCATED]" if len(sanitized) > 4000 else "")


def _shell_tokens(command: str) -> list[str]:
    """Return shell words and separators without failing closed on syntax.

    Claude may send an incomplete command while it is being composed. In that
    case a best-effort tokenization is preferable to crashing the hook; the
    regex SQL checks below still provide a safe fallback.
    """

    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|\n")
        lexer.whitespace_split = True
        return list(lexer)
    except (ValueError, TypeError):
        return command.split()


def _segments(tokens: Iterable[str]) -> Iterable[list[str]]:
    segment: list[str] = []
    find_action_terminator = False
    find_command = False
    for token in tokens:
        if token in _SHELL_SEPARATORS:
            if token == ";" and find_action_terminator:
                # shlex emits an escaped find `-exec ... \;` terminator as
                # the same punctuation token as a shell separator. Keep the
                # first one inside the find expression; a later bare `;`
                # still ends the shell segment.
                segment.append(token)
                find_action_terminator = False
                continue
            if segment:
                yield segment
                segment = []
            find_action_terminator = False
            find_command = False
            continue
        segment.append(token)
        if not find_command:
            executable_index = _executable_index(segment)
            if executable_index < len(segment):
                find_command = Path(segment[executable_index]).name.lower() == "find"
        if find_command and token in {"-exec", "-execdir", "-ok", "-okdir"}:
            find_action_terminator = True
        elif find_action_terminator and token in {";", "+"}:
            find_action_terminator = False
    if segment:
        yield segment


def _is_assignment(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token))


def _executable_index(segment: list[str]) -> int:
    """Find the executable after common environment and command wrappers."""

    index = 0
    sudo_options_with_values = {
        "-a", "-C", "--close-from", "-D", "--chdir", "-g",
        "--group", "-h", "--host", "-p", "--prompt", "-R", "--chroot",
        "-r", "--role", "-t", "--type", "-T", "--command-timeout", "-U",
        "--other-user", "-u", "--user",
    }
    env_options_with_values = {"-C", "--chdir", "-u", "--unset"}

    while index < len(segment):
        while index < len(segment) and _is_assignment(segment[index]):
            index += 1
        if index >= len(segment):
            return index

        executable = Path(segment[index]).name.lower()
        if executable == "env":
            index += 1
            while index < len(segment):
                token = segment[index]
                if _is_assignment(token) or token in {"-i", "--ignore-environment", "-0", "--null"}:
                    index += 1
                elif token in env_options_with_values:
                    index += 2
                elif token.startswith(("--chdir=", "--unset=")) or (
                    token.startswith("-u") and token != "-u"
                ):
                    index += 1
                elif token == "--":
                    index += 1
                    break
                elif token.startswith("-"):
                    # Options such as -v and -S do not consume a separate
                    # command operand here; -S's split command follows it.
                    index += 1
                else:
                    break
            continue

        if executable == "sudo":
            index += 1
            while index < len(segment):
                token = segment[index]
                if token == "--":
                    index += 1
                    break
                if token in sudo_options_with_values:
                    index += 2
                elif token.startswith("--") and "=" in token:
                    index += 1
                elif token.startswith("-"):
                    index += 1
                else:
                    break
            continue

        # These utilities execute one following command. Skip their options
        # and option operands so the destructive-command checks below inspect
        # the command that will actually run, not the wrapper itself.
        if executable in {"time", "nice", "timeout", "stdbuf"}:
            index += 1
            value_options = {
                "time": {"-f", "--format", "-o", "--output"},
                "nice": {"-n", "--adjustment"},
                "timeout": {"-k", "--kill-after", "-s", "--signal"},
                "stdbuf": {"-i", "--input", "-o", "--output", "-e", "--error"},
            }[executable]
            while index < len(segment):
                token = segment[index]
                if token == "--":
                    index += 1
                    break
                if token in value_options:
                    index += 2
                elif token.startswith("--") and "=" in token:
                    index += 1
                elif executable == "timeout" and token in {
                    "--foreground", "--preserve-status", "--verbose"
                }:
                    index += 1
                elif token.startswith("-"):
                    # Includes compact forms such as nice -n10 and
                    # timeout -sKILL; their values are part of the token.
                    index += 1
                elif executable == "timeout":
                    # timeout's first positional argument is its duration.
                    index += 1
                    break
                else:
                    break
            continue

        if executable in {"command", "builtin", "nohup"}:
            index += 1
            if index < len(segment) and segment[index] == "--":
                index += 1
            elif executable == "command":
                while index < len(segment) and segment[index] in {"-p", "-v", "-V"}:
                    index += 1
            continue

        # BusyBox exposes applets (including `rm`) as subcommands. Treat the
        # applet name as the executable so the same destructive-command rules
        # apply to `busybox rm -rf ...` as to a direct `rm -rf ...` call.
        if executable == "busybox":
            index += 1
            if index < len(segment) and segment[index] == "--":
                index += 1
            continue

        return index
    return index


def _env_split_script(segment: list[str]) -> str | None:
    """Return the command string passed to ``env -S`` when present."""

    index = 0
    while index < len(segment) and _is_assignment(segment[index]):
        index += 1
    if index >= len(segment) or Path(segment[index]).name.lower() != "env":
        return None

    args = segment[index + 1 :]
    position = 0
    while position < len(args):
        token = args[position]
        if token == "--":
            return None
        if token in {"-S", "--split-string"}:
            return args[position + 1] if position + 1 < len(args) else None
        if token.startswith("--split-string="):
            return token.partition("=")[2]
        if _is_assignment(token) or token in {"-i", "--ignore-environment", "-0", "--null"}:
            position += 1
        elif token in {"-C", "--chdir", "-u", "--unset"}:
            position += 2
        elif token.startswith(("--chdir=", "--unset=")) or (
            token.startswith("-u") and token != "-u"
        ):
            position += 1
        elif token.startswith("-"):
            position += 1
        else:
            return None
    return None


def _rm_reason(segment: list[str]) -> str | None:
    index = _executable_index(segment)
    if index >= len(segment) or Path(segment[index]).name != "rm":
        return None
    has_recursive = False
    has_force = False
    for token in segment[index + 1 :]:
        if token == "--":
            break
        if token == "--recursive":
            has_recursive = True
        elif token == "--force":
            has_force = True
        elif token.startswith("-") and not token.startswith("--"):
            flags = token[1:]
            has_recursive |= "r" in flags or "R" in flags
            has_force |= "f" in flags
    if has_recursive and has_force:
        return "rm with both recursive and force flags (rm -rf) can erase an entire tree."
    return None


def _git_config_override_reason(tokens: list[str], push_index: int) -> str | None:
    """Detect force-enabling Git config passed before a ``push`` subcommand.

    ``git -c remote.origin.push=+HEAD:main push origin`` has no force flag
    after ``push``, but Git uses that configured refspec when the command has
    no explicit refspec.  Inspecting only push arguments would therefore
    miss a history rewrite.  A config value injected with ``--config-env``
    cannot be read safely from the hook, so reject that narrow override rather
    than guessing whether it is safe.
    """

    position = 0
    while position < push_index:
        token = tokens[position]
        config: str | None = None
        config_from_environment = False
        if token == "-c" and position + 1 < push_index:
            config = tokens[position + 1]
            position += 2
        elif token.startswith("-c") and token != "-c":
            config = token[2:]
            position += 1
        elif token == "--config-env" and position + 1 < push_index:
            config = tokens[position + 1]
            config_from_environment = True
            position += 2
        elif token.startswith("--config-env="):
            config = token.partition("=")[2]
            config_from_environment = True
            position += 1
        else:
            position += 1

        if config is None:
            continue
        name, separator, value = config.partition("=")
        if not separator:
            continue
        if _GIT_REMOTE_PUSH_CONFIG_RE.fullmatch(name):
            if config_from_environment:
                return "a Git remote push configuration from the environment cannot be inspected safely."
            if value.lstrip().startswith("+"):
                return "a forced git push can rewrite shared history."
        elif _GIT_REMOTE_MIRROR_CONFIG_RE.fullmatch(name):
            if config_from_environment:
                return "a Git remote push configuration from the environment cannot be inspected safely."
            if value.strip().lower() in _GIT_TRUE_VALUES:
                return "a forced git push can rewrite shared history."
    return None


def _git_force_reason(segment: list[str]) -> str | None:
    index = _executable_index(segment)
    if index >= len(segment) or Path(segment[index]).name != "git":
        return None
    tokens = segment[index + 1 :]
    try:
        push_index = tokens.index("push")
    except ValueError:
        return None
    config_reason = _git_config_override_reason(tokens, push_index)
    if config_reason:
        return config_reason
    if any(
        token in {"--force", "--force-with-lease", "-f"}
        or token == "--mirror"
        or token.startswith("--force-with-lease=")
        or token.startswith("--force=")
        or token.startswith("+")
        for token in tokens[push_index + 1 :]
    ):
        return "a forced git push can rewrite shared history."
    return None


def _has_top_level_sql_where(statement_tail: str) -> bool:
    """Find a WHERE token outside SQL strings, comments, and subqueries."""

    index = 0
    depth = 0
    while index < len(statement_tail):
        if statement_tail.startswith("/*", index):
            end = statement_tail.find("*/", index + 2)
            index = len(statement_tail) if end < 0 else end + 2
            continue
        if statement_tail.startswith("--", index) or statement_tail[index] == "#":
            newline = statement_tail.find("\n", index + 1)
            index = len(statement_tail) if newline < 0 else newline + 1
            continue

        char = statement_tail[index]
        if char == "$":
            delimiter = _SQL_DOLLAR_QUOTE_RE.match(statement_tail, index)
            if delimiter:
                end = statement_tail.find(delimiter.group(), delimiter.end())
                index = len(statement_tail) if end < 0 else end + len(delimiter.group())
                continue
        if char in {"'", '"', "`", "["}:
            closing = "]" if char == "[" else char
            index += 1
            while index < len(statement_tail):
                if statement_tail[index] == "\\" and index + 1 < len(statement_tail):
                    index += 2
                    continue
                if statement_tail[index] == closing:
                    if index + 1 < len(statement_tail) and statement_tail[index + 1] == closing:
                        index += 2
                        continue
                    index += 1
                    break
                index += 1
            continue
        if char == "(":
            depth += 1
            index += 1
            continue
        if char == ")":
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 0 and (char.isalpha() or char == "_"):
            end = index + 1
            while end < len(statement_tail) and (
                statement_tail[end].isalnum() or statement_tail[end] in "_$"
            ):
                end += 1
            if statement_tail[index:end].upper() == "WHERE":
                return True
            index = end
            continue
        index += 1
    return False


def _sql_reason(segment: list[str]) -> str | None:
    """Detect destructive SQL while allowing ordinary echo/printing commands."""

    if not segment:
        return None
    executable_index = _executable_index(segment)
    # A segment containing only environment assignments (for example
    # ``DEBUG=1``) is valid shell input but has no executable.  Treat it as a
    # harmless no-op instead of allowing the detector itself to raise an
    # IndexError and make the hook noisy.
    if executable_index >= len(segment):
        return None
    executable = Path(segment[executable_index]).name.lower()
    text = " ".join(segment)
    # A literal shown with echo/printf, or a program merely containing SQL in
    # a source string, is not being executed. Cover direct SQL statements and
    # the common command-line SQL clients (including SQL contained in -c args).
    if executable in {"echo", "printf", "print", "cat", "grep", "rg"}:
        return None
    if executable not in _SQL_CLIENTS and executable not in {"drop", "truncate", "delete"}:
        return None
    if _SQL_DROP_RE.search(text):
        return "DROP TABLE is destructive and is blocked by this hook."
    if _SQL_TRUNCATE_RE.search(text):
        return "TRUNCATE is destructive and is blocked by this hook."
    for delete_match in _SQL_DELETE_RE.finditer(text):
        statement_tail = text[delete_match.end() :].split(";", 1)[0]
        if not _has_top_level_sql_where(statement_tail):
            return "DELETE FROM without a WHERE clause can remove every row."
    return None


def _wrapped_script(segment: list[str]) -> str | None:
    """Return the inline script from a common ``sh -c`` style wrapper.

    Claude often emits a shell wrapper when it needs a particular shell or
    flags.  The outer command itself is harmless, but the inline script is
    still executed by that shell and must go through the same detector.
    """

    index = _executable_index(segment)
    if index >= len(segment) or Path(segment[index]).name.lower() not in _SHELL_WRAPPERS:
        return None
    args = segment[index + 1 :]
    for position, token in enumerate(args):
        # ``sh -c SCRIPT`` and ``sh -lc SCRIPT`` are the common forms.  Shell
        # options may be combined (for example ``bash -ec SCRIPT``), so look
        # for ``c`` in a short-option cluster as well.  Long options and
        # unrelated operands are left alone to avoid treating their values as
        # executable shell source.
        if token in {"-c", "-lc", "-cl"} and position + 1 < len(args):
            return args[position + 1]
        if token.startswith("-") and not token.startswith("--") and "c" in token[1:]:
            if position + 1 < len(args):
                return args[position + 1]
    return None


def _embedded_commands(segment: list[str]) -> list[str]:
    """Return command text executed through common command tools."""

    index = _executable_index(segment)
    if index >= len(segment):
        return []
    executable = Path(segment[index]).name.lower()
    args = segment[index + 1 :]

    # eval reparses the joined arguments as shell source.
    if executable == "eval":
        command = " ".join(args)
        return [command] if command else []

    if executable == "find":
        commands = []
        position = 0
        while position < len(args):
            token = args[position]
            if token not in {"-exec", "-execdir", "-ok", "-okdir"}:
                position += 1
                continue
            end = position + 1
            while end < len(args) and args[end] not in {";", "+"}:
                end += 1
            command = args[position + 1 : end]
            if command:
                commands.append(shlex.join(command))
            position = min(end + 1, len(args))
        return commands

    if executable != "xargs":
        return []

    value_options = {
        "-a", "--arg-file", "-d", "--delimiter", "-E", "--eof", "-e",
        "-I", "--replace", "-i", "-L", "--max-lines", "-l", "-n",
        "--max-args", "-P", "--max-procs", "-s", "--max-chars",
    }
    flag_options = {
        "-0", "--null", "-r", "--no-run-if-empty", "-p", "--interactive",
        "-t", "--verbose", "-x", "--exit", "--show-limits",
    }
    position = 0
    while position < len(args):
        token = args[position]
        if token == "--":
            position += 1
            break
        if token in value_options:
            position += 2
        elif token in flag_options or (token.startswith("--") and "=" in token):
            position += 1
        elif token.startswith("-") and len(token) > 2 and token[1:2] in {
            "a", "d", "E", "e", "I", "i", "L", "l", "n", "P", "s"
        }:
            # GNU xargs accepts attached short-option operands, e.g. -I{}.
            position += 1
        elif token.startswith("-"):
            position += 1
        else:
            break
    command = args[position:]
    return [shlex.join(command)] if command else []


def _balanced_command_substitution(command: str, start: int) -> tuple[str, int] | None:
    """Return the body/end of a balanced ``$(...)`` or process substitution.

    Parentheses inside quotes and backticks do not affect the outer balance;
    nested shell groups and nested substitutions do. This is intentionally a
    small scanner, not a general-purpose Bash parser.
    """

    if start + 1 >= len(command) or command[start + 1] != "(":
        return None
    depth = 1
    index = start + 2
    quote: str | None = None
    escaped = False
    while index < len(command):
        char = command[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if quote == "'":
            if char == "'":
                quote = None
            index += 1
            continue
        if char == "\\" and quote != "'":
            escaped = True
            index += 1
            continue
        if quote == "`":
            if char == "`":
                quote = None
            index += 1
            continue
        if char == "`":
            quote = "`"
            index += 1
            continue
        if quote == '"':
            if char == '"':
                quote = None
                index += 1
                continue
            if command.startswith("$(", index):
                depth += 1
                index += 2
                continue
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if command.startswith("$(", index) or command.startswith("<(", index) or command.startswith(">(", index):
            depth += 1
            index += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return command[start + 2 : index], index + 1
        index += 1
    return None


def _backtick_substitution(command: str, start: int) -> tuple[str, int] | None:
    index = start + 1
    body: list[str] = []
    while index < len(command):
        char = command[index]
        if char == "\\" and index + 1 < len(command):
            next_char = command[index + 1]
            if next_char in {"$", "`", "\\"}:
                body.append(next_char)
            else:
                body.extend((char, next_char))
            index += 2
            continue
        if char == "`":
            return "".join(body), index + 1
        body.append(char)
        index += 1
    return None


def _shell_substitutions(command: str) -> Iterable[str]:
    """Yield executable command-substitution bodies, excluding single quotes."""

    index = 0
    quote: str | None = None
    while index < len(command):
        char = command[index]
        if quote == "'":
            if char == "'":
                quote = None
            index += 1
            continue
        if char == "\\":
            index += 2
            continue
        if quote == '"':
            if char == '"':
                quote = None
                index += 1
                continue
            if char == '`':
                parsed = _backtick_substitution(command, index)
                if parsed:
                    body, index = parsed
                    yield body
                    continue
            if command.startswith("$(", index):
                parsed = _balanced_command_substitution(command, index)
                if parsed:
                    body, index = parsed
                    yield body
                    continue
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == '`':
            parsed = _backtick_substitution(command, index)
            if parsed:
                body, index = parsed
                yield body
                continue
        if command.startswith("$(", index) or command.startswith("<(", index) or command.startswith(">(", index):
            parsed = _balanced_command_substitution(command, index)
            if parsed:
                body, index = parsed
                yield body
                continue
        index += 1


def detect_danger(command: str) -> str | None:
    """Return a human-readable block reason, or ``None`` for safe commands."""

    return _detect_danger(command, 0)


def _detect_danger(command: str, depth: int) -> str | None:
    if not isinstance(command, str) or not command.strip():
        return None
    if depth > _MAX_SHELL_NESTING:
        return "nested shell expansions exceed the inspection limit and are blocked conservatively."
    for substitution in _shell_substitutions(command):
        reason = _detect_danger(substitution, depth + 1)
        if reason:
            return reason
    tokens = _shell_tokens(command)
    for segment in _segments(tokens):
        split_script = _env_split_script(segment)
        if split_script is not None:
            reason = _detect_danger(split_script, depth + 1)
            if reason:
                return reason
        reason = _rm_reason(segment) or _git_force_reason(segment) or _sql_reason(segment)
        if reason:
            return reason
        for embedded in _embedded_commands(segment):
            reason = _detect_danger(embedded, depth + 1)
            if reason:
                return reason
        # Recursively inspect inline shell scripts such as
        # ``bash -lc 'git push --force origin main'``.  The depth is naturally
        # bounded by the command's token count, and an empty script is safe.
        wrapped = _wrapped_script(segment)
        if wrapped:
            reason = _detect_danger(wrapped, depth + 1)
            if reason:
                return reason
    return None


def _command_from_payload(payload: dict[str, Any]) -> str | None:
    tool_name = payload.get("tool_name")
    if tool_name is not None and not isinstance(tool_name, str):
        raise ValueError("invalid tool name")
    if tool_name not in {None, "Bash"}:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        raise ValueError("missing tool input")
    command = tool_input.get("command", tool_input.get("cmd"))
    if not isinstance(command, str):
        raise ValueError("missing command string")
    return command


def _hooks_dir() -> Path:
    return Path(os.environ.get("CLAUDE_HOOKS_DIR", str(Path.home() / ".claude" / "hooks"))).expanduser()


def _open_audit_log(log_path: Path, flags: int, mode: int) -> int:
    """Open the audit log without following a final-component link."""

    if os.name != "nt":
        return os.open(log_path, flags, mode)

    # Windows' os.open has no O_NOFOLLOW equivalent. Open the reparse point
    # itself with CreateFileW, inspect that same handle, and reject it before
    # converting the handle to a writable file descriptor. This avoids the
    # check-then-open race of Path.is_symlink().
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class FileAttributeTagInfo(ctypes.Structure):
        _fields_ = [
            ("FileAttributes", wintypes.DWORD),
            ("ReparseTag", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    get_file_information = kernel32.GetFileInformationByHandleEx
    get_file_information.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    get_file_information.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL

    file_append_data = 0x0004
    file_read_attributes = 0x0080
    file_share_all = 0x0001 | 0x0002 | 0x0004
    open_always = 4
    file_attribute_normal = 0x0080
    file_flag_open_reparse_point = 0x00200000
    file_attribute_reparse_point = 0x0400
    file_attribute_tag_info_class = 9
    invalid_handle_value = ctypes.c_void_p(-1).value

    handle = create_file(
        os.fspath(log_path),
        file_append_data | file_read_attributes,
        file_share_all,
        None,
        open_always,
        file_attribute_normal | file_flag_open_reparse_point,
        None,
    )
    if handle == invalid_handle_value:
        raise ctypes.WinError(ctypes.get_last_error())

    handle_owned = True
    try:
        tag_info = FileAttributeTagInfo()
        if not get_file_information(
            handle,
            file_attribute_tag_info_class,
            ctypes.byref(tag_info),
            ctypes.sizeof(tag_info),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if tag_info.FileAttributes & file_attribute_reparse_point:
            raise OSError(
                "refusing to append to a reparse-point audit log: "
                f"{log_path}"
            )

        fd = msvcrt.open_osfhandle(int(handle), os.O_WRONLY | os.O_APPEND)
        handle_owned = False  # The CRT file descriptor now owns the handle.
        return fd
    finally:
        if handle_owned:
            close_handle(handle)


def _log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    hooks_dir = _hooks_dir()
    log_path = Path(os.environ.get("CLAUDE_HOOK_LOG", str(hooks_dir / "blocked.log"))).expanduser()
    project_path = payload.get("cwd")
    if not isinstance(project_path, str) or not project_path:
        project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    project_path = project_path[:4000] + ("…[TRUNCATED]" if len(project_path) > 4000 else "")
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "attempted_command": _redact_command_for_log(command),
        "project_path": project_path,
        "reason": reason,
    }
    fd: int | None = None
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Fast-path obvious links; _open_audit_log also protects the actual
        # open against a link being substituted after this check.
        if log_path.is_symlink():
            raise OSError("Refusing to follow a symlink audit log")
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = _open_audit_log(log_path, flags, 0o600)
        if os.name == "posix":
            # Also restrict an existing log file, not just a newly created one.
            os.fchmod(fd, 0o600)
        log_file = os.fdopen(fd, "a", encoding="utf-8")
        fd = None  # ownership moved to log_file
        with log_file:
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except (OSError, TypeError, ValueError):
        # A logging failure must not allow a destructive operation through,
        # and must not make Claude's hook invocation fail noisily.
        pass
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def _write_deny(stdout: TextIO, reason: str) -> None:
    alternatives = {
        "rm with both recursive and force flags (rm -rf) can erase an entire tree.":
            "inspect the exact path first (for example with `git clean -nd`) and remove only the named target",
        "a forced git push can rewrite shared history.":
            "push a new branch normally; history rewrites require explicit human approval",
        "DROP TABLE is destructive and is blocked by this hook.":
            "use a reviewed migration with a backup and an explicit table name",
        "TRUNCATE is destructive and is blocked by this hook.":
            "use a reviewed, scoped transaction after previewing the rows to remove",
        "DELETE FROM without a WHERE clause can remove every row.":
            "add a narrowly scoped WHERE clause and run a SELECT preview first",
    }
    safe_alternative = alternatives.get(reason, "review the command and narrow its scope before retrying")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked by destructive-command-guard: {reason} "
                "The command was not run. Safe alternative: "
                f"{safe_alternative}."
            ),
        }
    }
    json.dump(output, stdout, ensure_ascii=False)
    stdout.write("\n")


def _deny_invalid_input(stdout: TextIO, payload: dict[str, Any] | None = None) -> None:
    reason = "invalid hook input; the command could not be inspected."
    _log_block(payload or {}, "[unavailable: invalid hook input]", reason)
    _write_deny(stdout, reason)


def main(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    try:
        payload = json.load(stdin)
    except (json.JSONDecodeError, TypeError, ValueError, UnicodeError):
        _deny_invalid_input(stdout)
        return 0
    if not isinstance(payload, dict):
        _deny_invalid_input(stdout)
        return 0
    try:
        command = _command_from_payload(payload)
    except (TypeError, ValueError):
        _deny_invalid_input(stdout, payload)
        return 0
    if command is None:  # A different explicitly named tool is outside this hook's scope.
        return 0
    reason = detect_danger(command)
    if reason:
        _log_block(payload, command, reason)
        _write_deny(stdout, reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
