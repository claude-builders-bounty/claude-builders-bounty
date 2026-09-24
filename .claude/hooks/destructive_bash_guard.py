#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive Bash commands.

The hook reads Claude Code's JSON event from stdin. It only evaluates Bash
tool calls, blocks destructive commands, logs the attempt, and returns a
structured deny decision. Harmless commands that merely *mention* dangerous
text (for example, `echo "rm -rf /"`) are allowed.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
import re
import shlex
import sys
from typing import Iterable, Optional

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

_SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
_SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd"}
_SEPARATORS = {";", "&&", "||", "|", "&"}
_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
_DROP_TABLE_RE = re.compile(r"(?is)\bdrop\s+table\b")
_TRUNCATE_RE = re.compile(r"(?is)\btruncate(?:\s+table)?\b")
_DELETE_RE = re.compile(r"(?is)\bdelete\s+from\b")


def _basename(token: str) -> str:
    return token.rsplit("/", 1)[-1].lower()


def _tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    return list(lexer)


def _segments(tokens: Iterable[str]) -> Iterable[list[str]]:
    current: list[str] = []
    for token in tokens:
        if token in _SEPARATORS or (token and set(token) <= set(";&|")):
            if current:
                yield current
                current = []
        else:
            current.append(token)
    if current:
        yield current


def _strip_wrappers(tokens: list[str]) -> list[str]:
    """Remove common command wrappers without scanning harmless arguments."""
    tokens = list(tokens)

    while tokens and _ASSIGNMENT_RE.match(tokens[0]):
        tokens.pop(0)

    changed = True
    while tokens and changed:
        changed = False
        exe = _basename(tokens[0])

        if exe == "command":
            tokens.pop(0)
            changed = True
            continue

        if exe == "env":
            tokens.pop(0)
            while tokens and (tokens[0].startswith("-") or _ASSIGNMENT_RE.match(tokens[0])):
                tokens.pop(0)
            changed = True
            continue

        if exe == "sudo":
            tokens.pop(0)
            options_with_value = {
                "-u", "--user", "-g", "--group", "-h", "--host",
                "-p", "--prompt", "-C", "--chdir", "-R", "--chroot",
            }
            while tokens and tokens[0].startswith("-"):
                opt = tokens.pop(0)
                if "=" not in opt and opt in options_with_value and tokens:
                    tokens.pop(0)
            changed = True
            continue

    return tokens


def _rm_is_recursive_force(args: list[str]) -> bool:
    recursive = False
    force = False
    for token in args:
        if token == "--":
            break
        if not token.startswith("-") or token == "-":
            continue
        if token in {"--recursive"}:
            recursive = True
        elif token in {"--force"}:
            force = True
        elif token.startswith("--"):
            continue
        else:
            flags = token[1:]
            recursive = recursive or ("r" in flags.lower())
            force = force or ("f" in flags.lower())
    return recursive and force


def _git_force_push(args: list[str]) -> bool:
    try:
        push_index = args.index("push")
    except ValueError:
        return False

    for token in args[push_index + 1:]:
        if token in {"--force", "--force-with-lease", "-f"}:
            return True
        if token.startswith("--force=") or token.startswith("--force-with-lease="):
            return True
        if token.startswith("-") and not token.startswith("--") and "f" in token[1:]:
            return True
    return False


def _strip_sql_string_literals(sql: str) -> str:
    # Remove single-quoted SQL string contents so harmless data such as
    # SELECT 'DROP TABLE users' does not trigger a false positive.
    return re.sub(r"'(?:''|[^'])*'", "''", sql)


def _delete_without_where(sql: str) -> bool:
    for statement in re.split(r";|\n", _strip_sql_string_literals(sql)):
        if _DELETE_RE.search(statement) and not re.search(r"(?is)\bwhere\b", statement):
            return True
    return False


def _sql_reason(sql: str) -> Optional[str]:
    normalized = _strip_sql_string_literals(sql)
    if _DROP_TABLE_RE.search(normalized):
        return "destructive SQL (`DROP TABLE`)"
    if _TRUNCATE_RE.search(normalized):
        return "destructive SQL (`TRUNCATE`)"
    if _delete_without_where(normalized):
        return "destructive SQL (`DELETE FROM` without a `WHERE` clause)"
    return None


def _segment_reason(tokens: list[str], depth: int = 0) -> Optional[str]:
    if depth > 4:
        return None

    tokens = _strip_wrappers(tokens)
    if not tokens:
        return None

    exe = _basename(tokens[0])
    args = tokens[1:]

    if exe == "rm" and _rm_is_recursive_force(args):
        return "recursive forced deletion (`rm -rf`)"

    if exe == "git" and _git_force_push(args):
        return "history-rewriting push (`git push --force`/force variant)"

    if exe in _SHELLS:
        for index, token in enumerate(args):
            if token == "-c" and index + 1 < len(args):
                return blocked_reason(args[index + 1], depth=depth + 1)
        return None

    if exe in _SQL_CLIENTS:
        return _sql_reason(" ".join(args))

    # Also recognize bare SQL entered directly as a command. These are not
    # valid ordinary shell commands, so this does not interfere with normal
    # Bash usage while keeping the matcher easy to validate in isolation.
    bare = " ".join(tokens)
    if exe in {"drop", "truncate", "delete"}:
        return _sql_reason(bare)

    return None


def blocked_reason(command: str, depth: int = 0) -> Optional[str]:
    """Return a blocking reason, or None if the Bash command is allowed."""
    try:
        tokens = _tokenize(command)
    except ValueError:
        # Let Claude Code's own permission system handle malformed shell input.
        return None

    for segment in _segments(tokens):
        reason = _segment_reason(segment, depth=depth)
        if reason:
            return reason
    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive command: {reason}. "
                "Use a safer, scoped alternative or ask the user for explicit approval."
            ),
        }
    }))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = str(event.get("cwd") or tool_input.get("cwd") or os.getcwd())
    try:
        log_block(command, project_path, reason)
    except OSError:
        # Logging failure must never turn a known-dangerous command into an allow.
        pass

    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
