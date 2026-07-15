#!/usr/bin/env python3
"""Deterministically block a small set of destructive Bash commands.

Claude Code invokes this script as a PreToolUse command hook. The hook reads
the event JSON from stdin and emits a deny decision only for Bash commands
that match an explicitly protected pattern.
"""

from __future__ import annotations

import datetime as _datetime
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


DEFAULT_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_ENV_VAR = "CLAUDE_DESTRUCTIVE_HOOK_LOG"

_RM_RF = re.compile(
    r"(?<![\w-])(?:[\w./-]+/)?rm\s+"
    r"(?:-[^\s;&|]*r[^\s;&|]*f[^\s;&|]*"
    r"|-[^\s;&|]*f[^\s;&|]*r[^\s;&|]*"
    r"|-[^\s;&|]*r[^\s;&|]*\s+-[^\s;&|]*f[^\s;&|]*"
    r"|-[^\s;&|]*f[^\s;&|]*\s+-[^\s;&|]*r[^\s;&|]*)"
    r"(?=\s|$)",
    re.IGNORECASE,
)
_FORCED_PUSH = re.compile(
    r"(?<![\w-])(?:[\w./-]+/)?git\s+push\b[^\n;|&]*"
    r"--force(?:-with-lease)?\b",
    re.IGNORECASE,
)
_DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
_TRUNCATE = re.compile(r"\btruncate\b", re.IGNORECASE)
_DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
_WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)

# These commands normally inspect or print text. Ignoring their arguments
# prevents false positives for commands such as:
#   echo "rm -rf is dangerous"
#   grep "DELETE FROM" migration.sql
_OBSERVATION_COMMANDS = {
    "awk",
    "cat",
    "cut",
    "diff",
    "echo",
    "false",
    "grep",
    "head",
    "less",
    "more",
    "printf",
    "rg",
    "ripgrep",
    "sed",
    "sort",
    "tail",
    "tee",
    "tr",
    "true",
    "uniq",
    "wc",
}
_OBSERVATION_GIT_SUBCOMMANDS = {
    "branch",
    "diff",
    "log",
    "reflog",
    "rev-parse",
    "show",
    "status",
    "tag",
}
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")


def split_shell_segments(command: str) -> List[str]:
    """Split shell control-flow segments without splitting quoted strings."""

    segments: List[str] = []
    current: List[str] = []
    quote: Optional[str] = None
    escaped = False
    index = 0

    while index < len(command):
        character = command[index]

        if escaped:
            current.append(character)
            escaped = False
            index += 1
            continue

        if character == "\\" and quote != "'":
            current.append(character)
            escaped = True
            index += 1
            continue

        if quote is not None:
            current.append(character)
            if character == quote:
                quote = None
            index += 1
            continue

        if character in ("'", '"'):
            quote = character
            current.append(character)
            index += 1
            continue

        if character in ("\n", ";"):
            segments.append("".join(current))
            current = []
            index += 1
            continue

        if character in ("&", "|"):
            segments.append("".join(current))
            current = []
            if index + 1 < len(command) and command[index + 1] == character:
                index += 2
            else:
                index += 1
            continue

        current.append(character)
        index += 1

    segments.append("".join(current))
    return segments


def _first_command_tokens(segment: str) -> List[str]:
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        # A malformed shell fragment is not treated as an observation command.
        return []

    while tokens and _ASSIGNMENT.fullmatch(tokens[0]):
        tokens.pop(0)
    return tokens


def _is_observation_command(segment: str) -> bool:
    tokens = _first_command_tokens(segment)
    if not tokens:
        return False

    executable = Path(tokens[0]).name.lower()
    if executable in _OBSERVATION_COMMANDS:
        return True

    if executable == "git" and len(tokens) > 1:
        return tokens[1].lower() in _OBSERVATION_GIT_SUBCOMMANDS

    return False


def _rm_has_recursive_force_flags(segment: str) -> bool:
    """Handle short flags split across tokens, including flags after operands."""

    tokens = _first_command_tokens(segment)
    rm_index: Optional[int] = None
    for index, token in enumerate(tokens):
        if Path(token).name.lower() == "rm":
            rm_index = index
            break

    if rm_index is None:
        return False

    short_flags = ""
    long_flags = set()
    for token in tokens[rm_index + 1 :]:
        if token == "--":
            break
        if token.startswith("--"):
            long_flags.add(token[2:].lower())
        elif token.startswith("-") and token != "-":
            short_flags += token[1:].lower()

    return (
        "r" in short_flags
        and "f" in short_flags
    ) or {"recursive", "force"}.issubset(long_flags)


def _delete_without_where(segment: str) -> bool:
    """Return True if any DELETE FROM statement lacks a WHERE clause."""

    for match in _DELETE_FROM.finditer(segment):
        tail = segment[match.end() :]
        boundary = re.search(r";|\n|&&|\|\|", tail)
        statement = tail if boundary is None else tail[: boundary.start()]
        if _WHERE.search(statement) is None:
            return True
    return False


def find_block_reason(command: str) -> Optional[str]:
    """Return a human-readable reason, or None when the command is allowed."""

    for segment in split_shell_segments(command):
        if _is_observation_command(segment):
            continue

        if _rm_has_recursive_force_flags(segment) or _RM_RF.search(segment):
            return "rm -rf/rm -fr recursively and forcibly removes files"
        if _FORCED_PUSH.search(segment):
            return "git push --force can overwrite remote history"
        if _DROP_TABLE.search(segment):
            return "DROP TABLE permanently removes a database table"
        if _TRUNCATE.search(segment):
            return "TRUNCATE removes all rows from a table or truncates a file"
        if _DELETE_FROM.search(segment) and _delete_without_where(segment):
            return "DELETE FROM without a WHERE clause can remove every row"

    return None


def _log_path() -> Path:
    configured = os.environ.get(LOG_ENV_VAR)
    return Path(configured).expanduser() if configured else DEFAULT_LOG_PATH


def append_block_log(command: str, cwd: str, reason: str) -> None:
    """Append one audit record and keep the log private when the OS permits."""

    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _datetime.datetime.now(_datetime.timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "command": command,
        "cwd": cwd,
        "reason": reason,
    }

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    try:
        path.chmod(0o600)
    except OSError:
        # Windows and some mounted filesystems may not support POSIX modes.
        pass


def _deny_payload(reason: str) -> Dict[str, object]:
    message = (
        f"Blocked destructive Bash command: {reason}. "
        "Rewrite the command with a narrow, reversible operation."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        },
        "systemMessage": message,
    }


def evaluate_event(event: Dict[str, object]) -> Optional[Tuple[str, str, str]]:
    """Return (command, cwd, reason) for a blocked event, otherwise None."""

    tool_name = str(event.get("tool_name") or "")
    if tool_name.lower() != "bash":
        return None

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    command = str(tool_input.get("command") or "")
    if not command.strip():
        return None

    reason = find_block_reason(command)
    if reason is None:
        return None

    cwd = str(event.get("cwd") or os.getcwd())
    return command, cwd, reason


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, TypeError):
        # A malformed hook event must not break Claude Code itself.
        return 0

    if not isinstance(event, dict):
        return 0

    blocked = evaluate_event(event)
    if blocked is None:
        return 0

    command, cwd, reason = blocked
    try:
        append_block_log(command, cwd, reason)
    except OSError:
        # Still deny the command if auditing fails. The decision is safer than
        # silently allowing a destructive operation.
        pass

    print(json.dumps(_deny_payload(reason), ensure_ascii=False))
    return 2


if __name__ == "__main__":
    sys.exit(main())
