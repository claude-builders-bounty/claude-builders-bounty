#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive Bash commands."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Optional

BLOCK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return command.split()


def detect_rm(tokens: list[str]) -> Optional[str]:
    for i, token in enumerate(tokens):
        if os.path.basename(token) != "rm":
            continue
        recursive = False
        force = False
        for arg in tokens[i + 1:]:
            if arg in {"&&", "||", ";", "|"}:
                break
            if arg == "--recursive":
                recursive = True
            elif arg == "--force":
                force = True
            elif arg.startswith("-") and not arg.startswith("--"):
                flags = arg[1:]
                recursive = recursive or "r" in flags or "R" in flags
                force = force or "f" in flags
        if recursive and force:
            return "Blocked recursive forced deletion (rm with recursive and force flags)."
    return None


def detect_forced_git_push(tokens: list[str]) -> Optional[str]:
    for i, token in enumerate(tokens):
        if os.path.basename(token) != "git":
            continue
        j = i + 1
        while j < len(tokens) and tokens[j].startswith("-"):
            j += 1
        if j >= len(tokens) or tokens[j] != "push":
            continue
        for arg in tokens[j + 1:]:
            if arg in {"&&", "||", ";", "|"}:
                break
            if arg in {"--force", "-f", "--force-with-lease"} or arg.startswith("--force-with-lease="):
                return "Blocked forced git push."
            if arg.startswith("+") and len(arg) > 1:
                return "Blocked forced git push via +refspec."
    return None


DROP_TABLE = re.compile(r"(?is)(?:^|[;&|]\s*)\s*drop\s+table\b")
TRUNCATE = re.compile(r"(?is)(?:^|[;&|]\s*)\s*truncate(?:\s+table)?\b")
DELETE_FROM = re.compile(r"(?is)(?:^|[;&|]\s*)\s*delete\s+from\b(?P<body>.*?)(?=(?:;|&&|\|\||\n|$))")


def detect_sql(command: str) -> Optional[str]:
    text = command.strip()
    if re.match(r"(?is)^\s*(?:echo|printf)\b", text):
        return None
    if DROP_TABLE.search(text):
        return "Blocked DROP TABLE statement."
    if TRUNCATE.search(text):
        return "Blocked TRUNCATE statement."
    for match in DELETE_FROM.finditer(text):
        if not re.search(r"(?i)\bwhere\b", match.group("body")):
            return "Blocked DELETE FROM statement without a WHERE clause."
    return None


def detect_danger(command: str) -> Optional[str]:
    tokens = shell_tokens(command)
    return detect_rm(tokens) or detect_forced_git_push(tokens) or detect_sql(command)


def audit(command: str, project_path: str, reason: str) -> None:
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with BLOCK_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload, separators=(",", ":")))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(event, dict):
        return 0
    if str(event.get("tool_name", "")).lower() not in {"bash", "shell"}:
        return 0
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0
    reason = detect_danger(command)
    if not reason:
        return 0
    project_path = str(event.get("cwd") or os.getcwd())
    try:
        audit(command, project_path, reason)
    except OSError:
        pass
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
