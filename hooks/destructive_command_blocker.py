#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path


COMMAND_SPLIT_RE = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")
DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def blocked_log_path() -> Path:
    hooks_home = os.environ.get("CLAUDE_HOOKS_HOME")
    if hooks_home:
        return Path(hooks_home).expanduser() / "hooks" / "blocked.log"
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def tokenize(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def skip_command_prefixes(tokens: list[str]) -> list[str]:
    """Skip common wrappers so `sudo rm -rf` and `env X=1 git push --force` block."""
    remaining = tokens[:]
    while remaining:
        head = remaining[0]
        if head == "sudo":
            remaining = remaining[1:]
            continue
        if head == "env":
            remaining = remaining[1:]
            while remaining and "=" in remaining[0] and not remaining[0].startswith("-"):
                remaining = remaining[1:]
            continue
        if re.match(r"^\w+=.+", head):
            remaining = remaining[1:]
            continue
        break
    return remaining


def rm_rf_reason(tokens: list[str]) -> str | None:
    tokens = skip_command_prefixes(tokens)
    if not tokens or tokens[0] != "rm":
        return None

    flags = [token for token in tokens[1:] if token.startswith("-")]
    short_flag_chars = "".join(flag.lstrip("-") for flag in flags if not flag.startswith("--"))
    has_recursive = "r" in short_flag_chars or "R" in short_flag_chars
    has_force = "f" in short_flag_chars
    has_recursive = has_recursive or any(flag in {"--recursive", "--dir"} for flag in flags)
    has_force = has_force or "--force" in flags
    has_recursive_force = has_recursive and has_force
    if has_recursive_force:
        return "rm -rf is destructive and can recursively delete project or system files."
    return None


def force_push_reason(tokens: list[str]) -> str | None:
    tokens = skip_command_prefixes(tokens)
    if len(tokens) < 3 or tokens[0:2] != ["git", "push"]:
        return None

    force_flags = {"--force", "-f", "--force-with-lease"}
    if any(token in force_flags or token.startswith("--force=") for token in tokens[2:]):
        return "git push --force can overwrite remote history and must be reviewed manually."
    return None


def sql_reason(statement: str) -> str | None:
    if DROP_TABLE_RE.search(statement):
        return "DROP TABLE can permanently remove database schema and data."
    if TRUNCATE_RE.search(statement):
        return "TRUNCATE can delete all rows from a table without row-by-row safeguards."
    if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
        return "DELETE FROM without WHERE can remove every row in the target table."
    return None


def block_reason(command: str) -> str | None:
    for segment in COMMAND_SPLIT_RE.split(command):
        if not segment.strip():
            continue

        tokens = tokenize(segment)
        for detector in (rm_rf_reason, force_push_reason):
            reason = detector(tokens)
            if reason:
                return reason

        reason = sql_reason(segment)
        if reason:
            return reason

    return None


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    path = blocked_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    path.open("a", encoding="utf-8").write(
        f"{timestamp}\tproject={project_path}\treason={reason}\tcommand={command}\n"
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Destructive command blocker could not parse hook JSON: {exc}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = block_reason(command)
    if not reason:
        return 0

    project_path = str(payload.get("cwd", "unknown"))
    log_blocked_attempt(command, project_path, reason)
    print(
        "Blocked destructive Bash command.\n"
        f"Reason: {reason}\n"
        f"Attempted command: {command}\n"
        "Use a narrower, reversible command or ask the user for explicit confirmation.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
