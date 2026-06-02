#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import errno
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any


BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Recursive forced rm is blocked by the destructive Bash guard.",
        re.compile(
            r"(?is)(?:^|[\s;&|()'\"])rm\s+"
            r"(?=[^;&|\n]*?(?:--recursive\b|-[^\s;&|]*r))"
            r"(?=[^;&|\n]*?(?:--force\b|-[^\s;&|]*f))"
        ),
    ),
    (
        "DROP TABLE is destructive SQL and is blocked by the destructive Bash guard.",
        re.compile(r"(?is)\bdrop\s+table\b"),
    ),
    (
        "TRUNCATE is destructive SQL and is blocked by the destructive Bash guard.",
        re.compile(r"(?is)\btruncate\s+table\s+[a-z_][\w.$\"]*"),
    ),
    (
        "Force-pushing can rewrite shared history and is blocked by the destructive Bash guard.",
        re.compile(r"(?is)\bgit\s+push\b[^\n;|&]*(?:--force(?:=\S+)?\b|--force-with-lease\b|(?<!\S)-f(?!\S))"),
    ),
)


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid hook JSON input: {exc}") from exc
    return payload if isinstance(payload, dict) else {}


def attempted_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "project_path"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def active_quote_before(command: str, index: int) -> str | None:
    quote: str | None = None
    escaped = False
    for char in command[:index]:
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote != "'":
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
        elif char in ("'", '"'):
            quote = char
    return quote


def sql_statement_from(command: str, start: int) -> str:
    quote = active_quote_before(command, start)
    for index in range(start, len(command)):
        char = command[index]
        if char == ";":
            return command[start:index]
        if quote:
            if char == quote:
                return command[start:index]
            continue
        if char in ("|", "&", "\n"):
            return command[start:index]
        if char in ("'", '"'):
            quote = char
    return command[start:]


def strip_sql_comments(statement: str) -> str:
    statement = re.sub(r"(?is)/\*.*?\*/", " ", statement)
    statement = re.sub(r"(?m)--[^\n]*", " ", statement)
    return statement


def strip_sql_strings(statement: str) -> str:
    return re.sub(r"(?is)'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", " ", statement)


def delete_from_without_where(command: str) -> str | None:
    for match in re.finditer(r"(?is)\bdelete\s+from\b", command):
        statement = sql_statement_from(command, match.start())
        searchable = strip_sql_strings(strip_sql_comments(statement))
        if not re.search(r"(?i)\bwhere\b", searchable):
            return "DELETE FROM without a WHERE clause is blocked by the destructive Bash guard."
    return None


def block_reason(command: str) -> str | None:
    for reason, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason
    return delete_from_without_where(command)


def redact_command(command: str) -> str:
    command = re.sub(r"(?i)\b(bearer)\s+[\w.:\-+/=]+", r"\1 [REDACTED]", command)
    command = re.sub(
        r"(?i)\b(token|api[_-]?key|password|passwd|secret)=('[^']*'|\"[^\"]*\"|[^\s;&|]+)",
        r"\1=[REDACTED]",
        command,
    )
    command = re.sub(r"(?i)(https?://)([^/\s:@]+):([^@\s/]+)@", r"\1[REDACTED]:[REDACTED]@", command)
    return command


def log_file_path() -> Path:
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def validate_opened_log_path(log_path: Path, fd: int) -> None:
    file_stat = os.fstat(fd)
    if not stat.S_ISREG(file_stat.st_mode):
        raise SystemExit(f"Refusing to write log because it is not a regular file: {log_path}")

    try:
        path_stat = log_path.lstat()
    except FileNotFoundError as exc:
        raise SystemExit(f"Refusing to write log because path changed during open: {log_path}") from exc

    if stat.S_ISLNK(path_stat.st_mode) or not os.path.samestat(path_stat, file_stat):
        raise SystemExit(f"Refusing to write log because path changed during open: {log_path}")

    os.fchmod(fd, 0o600)


def open_log_for_append(log_path: Path) -> int:
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    cloexec = getattr(os, "O_CLOEXEC", 0)
    if cloexec:
        flags |= cloexec
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow:
        flags |= nofollow
    try:
        existing_mode = log_path.lstat().st_mode
    except FileNotFoundError:
        existing_mode = None
    if existing_mode is not None and stat.S_ISLNK(existing_mode):
        raise SystemExit(f"Refusing to write log through symlink: {log_path}")
    try:
        fd = os.open(log_path, flags, 0o600)
    except OSError as exc:
        if nofollow and exc.errno in (errno.ELOOP, errno.EMLINK):
            raise SystemExit(f"Refusing to write log through symlink: {log_path}") from exc
        raise

    try:
        if os.name != "nt":
            validate_opened_log_path(log_path, fd)
        return fd
    except BaseException:
        os.close(fd)
        raise


def log_block(command: str, cwd: str, reason: str) -> None:
    log_path = log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project_path": cwd,
        "reason": reason,
        "attempted_command": redact_command(command),
    }
    line = (json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8")
    fd = open_log_for_append(log_path)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


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
    payload = read_payload()
    command = attempted_command(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    cwd = project_path(payload)
    log_block(command, cwd, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
