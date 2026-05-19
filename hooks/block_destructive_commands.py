#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DANGEROUS_PATTERNS = [
    (
        "DROP TABLE",
        re.compile(r"(?i)\bdrop\s+table\b"),
        "DROP TABLE permanently removes database tables.",
    ),
    (
        "git push --force",
        re.compile(r"(?i)\bgit\s+push\b[^;&|`]*--force(?:\b|-with-lease|=)"),
        "Force-pushing can overwrite shared Git history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"(?i)\btruncate(?:\s+table)?\b"),
        "TRUNCATE removes all rows from a table.",
    ),
]

RM_COMMAND = re.compile(r"(?i)(?:^|[;&|()`])\s*(?:sudo\s+)?rm\b(?P<args>[^;&|`]*)")
DELETE_FROM = re.compile(r"(?i)\bdelete\s+from\b")
WHERE_CLAUSE = re.compile(r"(?i)\bwhere\b")


def home_dir() -> Path:
    return Path(os.environ.get("HOME") or os.environ.get("USERPROFILE") or "~").expanduser()


def find_block_reason(command: str) -> str | None:
    """Return the block reason for a destructive command, otherwise None."""
    if not command:
        return None

    rm_reason = find_rm_rf(command)
    if rm_reason:
        return rm_reason

    for label, pattern, explanation in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return f"Blocked destructive Bash command ({label}): {explanation}"

    delete_reason = find_delete_without_where(command)
    if delete_reason:
        return delete_reason

    return None


def find_rm_rf(command: str) -> str | None:
    """Block rm invocations that combine recursive and force flags."""
    for match in RM_COMMAND.finditer(command):
        args = match.group("args")
        try:
            tokens = shlex.split(args)
        except ValueError:
            tokens = args.split()

        recursive = False
        force = False
        for token in tokens:
            if token == "--":
                break
            if token.startswith("--"):
                option = token.split("=", 1)[0].lower()
                recursive = recursive or option == "--recursive"
                force = force or option == "--force"
            elif token.startswith("-") and len(token) > 1:
                flags = token[1:].lower()
                recursive = recursive or "r" in flags
                force = force or "f" in flags

        if recursive and force:
            return (
                "Blocked destructive Bash command (rm -rf): "
                "Recursive forced deletion can remove large parts of the filesystem."
            )
    return None


def find_delete_without_where(command: str) -> str | None:
    """Block DELETE FROM statements unless the same SQL statement has WHERE."""
    for match in DELETE_FROM.finditer(command):
        statement = command[match.start() :]
        statement = statement.split(";", 1)[0]
        if not WHERE_CLAUSE.search(statement):
            return (
                "Blocked destructive Bash command (DELETE FROM without WHERE): "
                "DELETE FROM without a WHERE clause can remove every matching row."
            )
    return None


def evaluate_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    if payload.get("hook_event_name") != "PreToolUse":
        return None
    if payload.get("tool_name") != "Bash":
        return None

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = find_block_reason(command)
    if reason is None:
        return None

    log_blocked_attempt(command, reason, str(payload.get("cwd") or ""))
    return deny_decision(reason)


def deny_decision(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def log_blocked_attempt(command: str, reason: str, project_path: str) -> None:
    hooks_dir = home_dir() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def install_hook() -> None:
    claude_dir = home_dir() / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        settings = {}

    settings.setdefault("hooks", {})
    pre_tool_use = settings["hooks"].setdefault("PreToolUse", [])
    hook_path = hooks_dir / "block_destructive_commands.py"
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(hook_path))}"
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }

    if not any(existing == entry for existing in pre_tool_use):
        pre_tool_use.append(entry)

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed Bash safety hook in {settings_path}")


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Register this hook in ~/.claude/settings.json")
    args = parser.parse_args()

    if args.install:
        install_hook()
        return 0

    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        print(f"Invalid Claude Code hook JSON: {exc}", file=sys.stderr)
        return 1

    decision = evaluate_payload(payload)
    if decision is not None:
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
