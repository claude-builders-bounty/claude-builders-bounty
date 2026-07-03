#!/usr/bin/env python3
"""Claude Code pre-tool-use hook for blocking destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO


LOG_PATH_ENV = "CLAUDE_BLOCKED_COMMANDS_LOG"


@dataclass(frozen=True)
class CommandDecision:
    blocked: bool
    reason: str = ""


def default_log_path() -> Path:
    home = os.environ.get("HOME")
    base = Path(home) if home else Path.home()
    return base / ".claude" / "hooks" / "blocked.log"


def classify_command(command: str) -> CommandDecision:
    if _contains_rm_rf(command):
        return CommandDecision(True, "Blocked rm -rf because it can recursively delete files.")
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return CommandDecision(True, "Blocked DROP TABLE because it can destroy database schema.")
    if _contains_force_push(command):
        return CommandDecision(True, "Blocked git push --force because it can rewrite shared history.")
    if re.search(r"\btruncate(?:\s+table)?\b", command, flags=re.IGNORECASE):
        return CommandDecision(True, "Blocked TRUNCATE because it can remove table data.")
    if _contains_unscoped_delete(command):
        return CommandDecision(
            True,
            "Blocked DELETE FROM without WHERE because it can remove all matching rows.",
        )
    return CommandDecision(False)


def _contains_rm_rf(command: str) -> bool:
    return bool(
        re.search(r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-[A-Za-z]*f[A-Za-z]*r)\b", command)
        or re.search(
            r"\brm\b(?=.*\b--recursive\b)(?=.*\b--force\b)",
            command,
            flags=re.IGNORECASE,
        )
    )


def _contains_force_push(command: str) -> bool:
    return bool(
        re.search(
            r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-\w+)?|(?:^|\s)-f(?:\s|$))",
            command,
            flags=re.IGNORECASE,
        )
    )


def _contains_unscoped_delete(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b",
            statement,
            flags=re.IGNORECASE,
        ):
            return True
    return False


def main(stdin: TextIO = sys.stdin, log_path: Path | None = None) -> int:
    try:
        payload = json.loads(stdin.read().lstrip("\ufeff"))
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    if not command:
        return 0

    decision = classify_command(command)
    if not decision.blocked:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    log_blocked_attempt(
        command=command,
        project_path=project_path,
        log_path=log_path or configured_log_path(),
    )

    message = f"Blocked destructive command: {decision.reason}"
    print(message, file=sys.stderr)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            },
            separators=(",", ":"),
        )
    )
    return 0


def configured_log_path() -> Path:
    override = os.environ.get(LOG_PATH_ENV)
    return Path(override) if override else default_log_path()


def log_blocked_attempt(command: str, project_path: str, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    record = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
