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

BLOCKED_LOG = Path(
    os.environ.get("CLAUDE_HOOKS_BLOCKED_LOG", "~/.claude/hooks/blocked.log")
).expanduser()


def is_rm_rf(command: str) -> bool:
    """Detect `rm` invocations that include both recursive and force flags."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False

    for idx, token in enumerate(tokens):
        if token != "rm":
            continue

        has_recursive = False
        has_force = False

        for arg in tokens[idx + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-"):
                continue
            if arg == "--recursive":
                has_recursive = True
            elif arg == "--force":
                has_force = True
            elif arg.startswith("--"):
                continue
            else:
                flags = arg[1:]
                if "r" in flags or "R" in flags:
                    has_recursive = True
                if "f" in flags:
                    has_force = True

        if has_recursive and has_force:
            return True

    return False


def normalize_sql(command: str) -> str:
    return " ".join(command.lower().split())


def has_delete_without_where(command: str) -> bool:
    compact = normalize_sql(command)
    for match in re.finditer(r"delete\s+from\s+", compact):
        trailing = compact[match.end() :]
        segment = re.split(r"[;&|]", trailing, maxsplit=1)[0]
        if " where " not in f" {segment} ":
            return True
    return False


def blocked_reason(command: str) -> str | None:
    compact = normalize_sql(command)

    if is_rm_rf(command):
        return "Blocked: recursive forced delete (`rm -rf`/`rm -fr`)"
    if re.search(r"\bdrop\s+table\b", compact):
        return "Blocked: SQL schema destruction (`DROP TABLE`)"
    if re.search(r"\btruncate\b", compact):
        return "Blocked: SQL truncation (`TRUNCATE`)"
    if re.search(r"\bgit\s+push\b", compact) and re.search(r"\s--force(?:\s|$)|\s-f(?:\s|$)", compact):
        return "Blocked: force push (`git push --force` / `git push -f`)"
    if has_delete_without_where(command):
        return "Blocked: `DELETE FROM` without a `WHERE` clause"

    return None


def append_log(command: str, project_path: str, reason: str) -> bool:
    timestamp = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    try:
        BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
            handle.write(
                f"[{timestamp}] project={project_path} reason={reason} command={command}\n"
            )
        return True
    except OSError:
        return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Hook input JSON parse error: {exc}", file=sys.stderr)
        return 1

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "").strip()
    if not command:
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    logged = append_log(command, project_path, reason)

    print(reason, file=sys.stderr)
    if not logged:
        print(
            f"Warning: could not write log file at {BLOCKED_LOG}",
            file=sys.stderr,
        )
    print("This command was blocked by the pre-tool-use safety hook.", file=sys.stderr)
    print("If this is intentional, run it manually after explicit human review.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
