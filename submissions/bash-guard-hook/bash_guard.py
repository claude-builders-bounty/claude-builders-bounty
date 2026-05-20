#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads Claude Code hook JSON from stdin and exits non-zero when the Bash command
matches a destructive pattern.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm-rf",
        re.compile(r"(^|[;&|\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-f[A-Za-z]*r|-[A-Za-z]*rf)\b", re.I),
        "Blocks recursive forced removal (`rm -rf`).",
    ),
    (
        "drop-table",
        re.compile(r"\bdrop\s+table\b", re.I),
        "Blocks SQL table drops.",
    ),
    (
        "git-force-push",
        re.compile(r"\bgit\s+push\b[^\n]*(?:--force(?:-with-lease)?\b|\s-f\b)", re.I),
        "Blocks force-pushing git history.",
    ),
    (
        "truncate",
        re.compile(r"\btruncate\b", re.I),
        "Blocks SQL truncate operations.",
    ),
]

DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.I)
WHERE = re.compile(r"\bwhere\b", re.I)


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("cmd") or "")
    return ""


def project_path(payload: dict) -> str:
    return str(payload.get("cwd") or payload.get("project_path") or os.getcwd())


def blocked_rule(command: str) -> tuple[str, str] | None:
    for name, pattern, message in RULES:
        if pattern.search(command):
            return name, message
    if DELETE_FROM.search(command) and not WHERE.search(command):
        return "delete-from-without-where", "Blocks DELETE FROM statements without a WHERE clause."
    return None


def log_block(rule: str, command: str, cwd: str) -> Path:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp}\t{cwd}\t{rule}\t{safe_command}\n")
    return log_path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"bash_guard: invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    result = blocked_rule(command)
    if not result:
        return 0

    rule, message = result
    cwd = project_path(payload)
    log_path = log_block(rule, command, cwd)
    print(
        "Blocked destructive Bash command before execution.\n"
        f"Rule: {rule}\n"
        f"Reason: {message}\n"
        f"Project: {cwd}\n"
        f"Log: {log_path}\n"
        "If this operation is truly intended, run it manually after reviewing backups and blast radius.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
