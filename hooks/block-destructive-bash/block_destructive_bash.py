#!/usr/bin/env python3
r"""Claude Code PreToolUse hook — blocks destructive bash commands.

Wire it up in ~/.claude/settings.json (see settings.example.json):

    {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3 ~/.claude/hooks/block_destructive_bash.py"}
    ]}]}}

Blocked patterns
    rm -rf (any flag order / combined short flags)      -> rule rm_rf
    DROP TABLE / DROP DATABASE / DROP SCHEMA ...        -> rule drop_table
    TRUNCATE (SQL)                                      -> rule truncate
    DELETE FROM ... without WHERE                       -> rule delete_without_where
    git push --force / -f (force-with-lease allowed)    -> rule git_force_push

Every block is appended to ~/.claude/hooks/blocked.log as one JSON line with
timestamp, command and project path, and the reason is returned to Claude so it
can choose a safe alternative instead of retrying blindly.

Escape hatches (deliberate, documented):
    BLOCK_DESTRUCTIVE_BASH_ALLOW='rm -rf (node_modules|dist|\.next)'  regex whitelist
    BLOCK_DESTRUCTIVE_BASH_MODE=exit2    older Claude Code: exit 2 + stderr
    BLOCK_DESTRUCTIVE_BASH_LOG=/path     different audit log

Exit codes
    0  allow (also: every parse failure — a broken hook must never wedge a session)
    2  blocked (only in exit2 mode)
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path

LOG_PATH = Path(
    os.environ.get(
        "BLOCK_DESTRUCTIVE_BASH_LOG", str(Path.home() / ".claude" / "hooks" / "blocked.log")
    )
)
MODE = os.environ.get("BLOCK_DESTRUCTIVE_BASH_MODE", "json").strip().lower()
ALLOW_RE = os.environ.get("BLOCK_DESTRUCTIVE_BASH_ALLOW", "").strip()

_SEGMENT_SPLIT = re.compile(r"(?:&&|\|\||;|\n|(?<![|])\|(?![|]))")
_WRAPPERS = {"sudo", "env", "command", "time", "nice", "nohup", "exec", "xargs", "stdbuf"}
_SQL_HINT = re.compile(
    r"\b(?:select|insert\s+into|update\s+\w+\s+set|delete\s+from|drop\s+(?:table|database|schema|view|index)"
    r"|truncate|alter\s+table|create\s+(?:table|index))\b",
    re.IGNORECASE,
)
_SQL_CLIENTS = re.compile(r"\b(sqlite3|mysql|mariadb|psql|sqlplus|duckdb)\b", re.IGNORECASE)


def _tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment, comments=False, posix=True)
    except ValueError:  # unbalanced quote — fall back to a dumb split
        return segment.split()


def _strip_wrappers(tokens: list[str]) -> list[str]:
    i = 0
    while i < len(tokens):
        base = os.path.basename(tokens[i])
        if base in _WRAPPERS:
            i += 1
            # skip wrapper flags, e.g. `env FOO=1`, `nice -n 10`
            while i < len(tokens) and (tokens[i].startswith("-") or "=" in tokens[i]):
                i += 1
            continue
        break
    return tokens[i:]


def _short_flags(tokens: list[str]) -> set[str]:
    """`-rf`, `-fr`, `-Rf` -> {'r','f'}; plus long options as-is."""
    flags: set[str] = set()
    for tok in tokens:
        if not tok.startswith("-") or tok == "--":
            continue
        if tok.startswith("--"):
            flags.add(tok.lower())
            continue
        flags.update(ch for ch in tok[1:] if ch.isalpha())
    return flags


def _rm_targets(tokens: list[str]) -> list[str]:
    targets: list[str] = []
    for tok in tokens[1:]:
        if tok.startswith("-"):
            continue
        targets.append(tok)
    return targets


def check_rm_rf(command: str) -> str | None:
    for segment in _SEGMENT_SPLIT.split(command):
        tokens = _strip_wrappers(_tokens(segment))
        if not tokens:
            continue
        if os.path.basename(tokens[0]).lower() not in {"rm", "rm.exe"}:
            continue
        flags = _short_flags(tokens)
        recursive = bool({"r", "--recursive", "--no-preserve-root"} & flags)
        forced = bool({"f", "--force"} & flags)
        if recursive and forced:
            return (
                "rm -rf permanently deletes files with no way back. "
                "Use `rm -ri <path>` (prompts per file), move the target to a "
                "trash directory, or scope the delete to a build artifact you can regenerate."
            )
    return None


def check_drop_table(command: str) -> str | None:
    if not _SQL_HINT.search(command):
        return None
    if re.search(r"\bdrop\s+(?:table|database|schema|view|index)\b", command, re.IGNORECASE):
        return (
            "DROP removes a schema object and its data irreversibly. "
            "Write a migration with an explicit down path, or use "
            "`ALTER TABLE ... RENAME TO ..._backup_<date>` so the data survives."
        )
    return None


def check_truncate(command: str) -> str | None:
    if not re.search(r"\btruncate\b", command, re.IGNORECASE):
        return None
    # `truncate -s 0 file` is coreutils, not SQL — do not block it here.
    if re.search(r"\btruncate\s+table\b", command, re.IGNORECASE) or _SQL_CLIENTS.search(command):
        return (
            "TRUNCATE empties a table and cannot be rolled back outside a transaction. "
            "Use `DELETE FROM ... WHERE ...` inside a transaction, or copy the table first."
        )
    return None


def check_delete_without_where(command: str) -> str | None:
    if not re.search(r"\bdelete\s+from\b", command, re.IGNORECASE):
        return None
    for statement in command.split(";"):
        if not re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE):
            continue
        if re.search(r"\bwhere\b", statement, re.IGNORECASE):
            continue
        return (
            "DELETE FROM without a WHERE clause removes every row in the table. "
            "Add a WHERE predicate, or run the same statement inside a transaction "
            "and `SELECT count(*)` first."
        )
    return None


def check_git_force_push(command: str) -> str | None:
    for segment in _SEGMENT_SPLIT.split(command):
        tokens = _strip_wrappers(_tokens(segment))
        if len(tokens) < 2 or os.path.basename(tokens[0]).lower() not in {"git", "git.exe"}:
            continue
        if "push" not in tokens[1:2] and "push" not in tokens:
            continue
        if "--force-with-lease" in tokens or "--force-if-includes" in tokens:
            continue
        for tok in tokens:
            if tok in {"--force", "-f"} or tok.startswith("+"):
                return (
                    "`git push --force` rewrites shared history and can erase other people's commits. "
                    "Use `git push --force-with-lease` (refuses when the remote moved), or push a new branch."
                )
    return None


RULES = (
    ("rm_rf", check_rm_rf),
    ("drop_table", check_drop_table),
    ("truncate", check_truncate),
    ("delete_without_where", check_delete_without_where),
    ("git_force_push", check_git_force_push),
)


def evaluate(command: str, cwd: str = "") -> tuple[str, str] | None:
    """Return (rule, reason) when the command must be blocked, else None."""
    if not command or not command.strip():
        return None
    if ALLOW_RE and re.search(ALLOW_RE, command):
        return None
    for rule, fn in RULES:
        reason = fn(command)
        if reason:
            return rule, reason
    return None


def _log(rule: str, command: str, cwd: str) -> None:
    record = {
        "ts": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "decision": "deny",
        "rule": rule,
        "cwd": cwd or os.getcwd(),
        "command": command.replace("\r", ""),
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:  # logging must never block the decision
        print(f"block_destructive_bash: cannot write log {LOG_PATH}: {exc}", file=sys.stderr)


def _deny(rule: str, reason: str, command: str, cwd: str) -> int:
    _log(rule, command, cwd)
    message = f"BLOCKED by block-destructive-bash [{rule}]: {reason}"
    if MODE == "exit2":
        print(message, file=sys.stderr)
        return 2
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        },
        "systemMessage": f"🛑 {message}",
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def main(argv: list[str]) -> int:
    # manual check: `python3 block_destructive_bash.py --check "rm -rf /"`
    if len(argv) >= 3 and argv[1] == "--check":
        command = " ".join(argv[2:])
        verdict = evaluate(command)
        if verdict:
            print(f"DENY [{verdict[0]}] {verdict[1]}")
            return 2
        print("ALLOW")
        return 0

    try:
        raw = sys.stdin.read()
        event = json.loads(raw or "{}")
    except (json.JSONDecodeError, OSError):
        return 0  # malformed input must not wedge the session

    # only Bash tool calls; anything else passes straight through
    if event.get("tool_name") not in (None, "Bash"):
        return 0

    command = str((event.get("tool_input") or {}).get("command") or "")
    cwd = str(event.get("cwd") or "")
    verdict = evaluate(command, cwd)
    if not verdict:
        return 0
    return _deny(verdict[0], verdict[1], command, cwd)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
