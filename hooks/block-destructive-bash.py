#!/usr/bin/env python3
"""Block a small, explicit set of destructive Bash commands for Claude Code.

The hook reads a Claude Code PreToolUse event from stdin. It emits a structured
PreToolUse denial on stdout when a dangerous command is detected and records the
attempt in ~/.claude/hooks/blocked.log.

The implementation intentionally uses only Python's standard library so the
hook can be installed without jq, third-party packages, or a virtualenv.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
SQL_CLIENTS = {
    "cockroach",
    "duckdb",
    "mariadb",
    "mysql",
    "psql",
    "sqlite3",
    "sqlcmd",
}
COMMAND_SEPARATORS = {";", "&&", "||", "|", "&"}


@dataclass(frozen=True)
class Finding:
    """A matched destructive command and the human-readable reason."""

    reason: str


def _tokenize(command: str) -> List[str]:
    """Tokenize shell syntax while preserving quoted arguments.

    This is deliberately not a shell interpreter. It only needs enough syntax
    awareness to distinguish ``echo \"rm -rf\"`` from an actual ``rm -rf`` and
    to inspect each command in a simple ``&&``/``;`` chain independently.
    """

    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        # An unterminated quote should not make the guard crash. Returning the
        # raw command as one segment still lets the direct SQL checks protect
        # the most obvious cases.
        return [command]


def _segments(tokens: Iterable[str]) -> Iterable[List[str]]:
    segment: List[str] = []
    for token in tokens:
        if token in COMMAND_SEPARATORS:
            if segment:
                yield segment
                segment = []
        else:
            segment.append(token)
    if segment:
        yield segment


def _first_command_index(segment: List[str]) -> Optional[int]:
    """Return the token index of the executable after common prefixes."""

    index = 0
    while index < len(segment):
        token = segment[index]
        if token in {"sudo", "command", "exec"}:
            index += 1
            continue
        if token == "env":
            index += 1
            while index < len(segment):
                option = segment[index]
                if option == "--":
                    index += 1
                    break
                if option in {"-u", "--unset"}:
                    index += 2
                    continue
                if option.startswith("-"):
                    index += 1
                    continue
                if "=" in option and not option.startswith("="):
                    index += 1
                    continue
                break
            continue
        if "=" in token and not token.startswith("=") and not token.startswith("-"):
            # Environment assignment such as DATABASE_URL=... command ...
            index += 1
            continue
        return index
    return None


def _first_command(segment: List[str]) -> Optional[str]:
    """Return the basename of the executable after common shell prefixes."""

    index = _first_command_index(segment)
    if index is None:
        return None
    return Path(segment[index]).name


def _rm_is_recursive_and_forced(segment: List[str]) -> bool:
    command_index = _first_command_index(segment)
    first = _first_command(segment)
    if first != "rm":
        return False

    recursive = False
    forced = False
    for token in segment[(command_index or 0) + 1 :]:
        if token == "--":
            break
        if token == "--recursive":
            recursive = True
            continue
        if token == "--force":
            forced = True
            continue
        if token.startswith("-") and token != "-":
            flags = token[1:]
            # Long options other than the two explicit names are not treated
            # as destructive flags. Short clusters such as -rf and -fr are.
            if not token.startswith("--"):
                recursive = recursive or "r" in flags or "R" in flags
                forced = forced or "f" in flags
            continue
    return recursive and forced


def _git_push_is_forced(segment: List[str]) -> bool:
    command_index = _first_command_index(segment)
    first = _first_command(segment)
    if first != "git":
        return False

    # Support common global options such as `git -C repo push --force`.
    try:
        push_index = next(
            index
            for index, token in enumerate(
                segment[(command_index or 0) + 1 :],
                start=(command_index or 0) + 1,
            )
            if token == "push"
        )
    except StopIteration:
        return False

    for token in segment[push_index + 1 :]:
        if token in {"--force", "-f"} or token.startswith("--force-"):
            return True
        if token.startswith("-") and not token.startswith("--") and "f" in token[1:]:
            return True
        if token == "--":
            break
    return False


def _has_unrestricted_delete(sql: str) -> bool:
    """Return True for DELETE FROM statements with no WHERE clause."""

    lowered = sql.lower()
    marker = "delete from"
    start = 0
    while True:
        index = lowered.find(marker, start)
        if index == -1:
            return False
        tail = lowered[index + len(marker) :]
        if "where" not in tail:
            return True
        # A WHERE after the next statement does not protect this statement.
        statement_tail = tail.split(";", 1)[0]
        if "where" not in statement_tail:
            return True
        start = index + len(marker)


def _sql_finding(segment: List[str]) -> Optional[Finding]:
    first = (_first_command(segment) or "").lower()
    if first not in SQL_CLIENTS and first not in {"drop", "truncate", "delete"}:
        return None

    sql = " ".join(segment)
    lowered = sql.lower()
    if "drop table" in lowered:
        return Finding("DROP TABLE statements are blocked")
    if "truncate" in lowered:
        return Finding("TRUNCATE statements are blocked")
    if _has_unrestricted_delete(sql):
        return Finding("DELETE FROM without a WHERE clause is blocked")
    return None


def find_finding(command: str) -> Optional[Finding]:
    """Return the first matching destructive-command finding, if any."""

    for segment in _segments(_tokenize(command)):
        if _rm_is_recursive_and_forced(segment):
            return Finding("rm -rf is blocked")
        if _git_push_is_forced(segment):
            return Finding("git push --force is blocked")
        sql_finding = _sql_finding(segment)
        if sql_finding is not None:
            return sql_finding
    return None


def _write_log(*, reason: str, command: str, cwd: str) -> Optional[str]:
    """Append one structured, human-readable record to the block log."""

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = "\t".join(
        [
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "reason=" + json.dumps(reason, ensure_ascii=False),
            "cwd=" + json.dumps(cwd, ensure_ascii=False),
            "command=" + json.dumps(command, ensure_ascii=False),
        ]
    )
    try:
        descriptor = os.open(
            LOG_PATH,
            os.O_APPEND | os.O_CREAT | os.O_WRONLY,
            0o600,
        )
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(record + "\n")
    except OSError as error:
        return str(error)
    return None


def _deny(reason: str, log_error: Optional[str]) -> None:
    if log_error:
        reason = f"{reason}. The block was kept because the attempt log could not be written: {log_error}"
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked by destructive-command guard: {reason}. "
                        "If this is intentional, run it manually outside Claude Code."
                    ),
                }
            }
        )
    )


def main() -> int:
    try:
        payload: Any = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        # A malformed event is not a reason to break an otherwise normal Bash
        # call. Claude Code will report the malformed hook input separately.
        return 0

    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    finding = find_finding(command)
    if finding is None:
        return 0

    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        cwd = os.getcwd()
    log_error = _write_log(reason=finding.reason, command=command, cwd=cwd)
    _deny(finding.reason, log_error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
