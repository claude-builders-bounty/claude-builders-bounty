#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive shell commands.

The program reads one Claude Code hook event from stdin and emits a JSON
decision only when the Bash command matches a destructive pattern.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _command_segments(command: str) -> list[str]:
    """Split common shell command separators without trying to parse Bash."""

    return [segment.strip() for segment in re.split(r"(?:&&|\|\||[;|\n])", command) if segment.strip()]


def _has_rm_rf(command: str) -> bool:
    """Return true for rm invocations that combine recursive and force flags."""

    for match in re.finditer(r"(?<![\w-])rm\s+([^;&|\n]*)", command, re.IGNORECASE):
        args = match.group(1)
        short_flags = "".join(re.findall(r"(?<!\w)-([A-Za-z]+)(?=\s|$)", args))
        has_recursive = "r" in short_flags.lower()
        has_force = "f" in short_flags.lower()
        long_flags = {flag.lower() for flag in re.findall(r"--([A-Za-z-]+)", args)}
        has_recursive = has_recursive or "recursive" in long_flags
        has_force = has_force or "force" in long_flags
        if has_recursive and has_force:
            return True
    return False


def _has_force_push(command: str) -> bool:
    for match in re.finditer(r"(?<![\w-])git\s+push\b([^;&|\n]*)", command, re.IGNORECASE):
        args = match.group(1)
        if re.search(r"(?:^|\s)(?:-f|--force(?:-with-lease)?)(?=\s|$)", args, re.IGNORECASE):
            return True
    return False


def _has_delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement = command[match.start() :]
        statement = re.split(r"(?:;|&&|\|\||\||\n)", statement, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def detect_block_reason(command: str) -> str | None:
    """Return a human-readable block reason, or None for an allowed command."""

    if _has_rm_rf(command):
        return "rm with both recursive and force flags"
    if _has_force_push(command):
        return "a forced git push"
    if re.search(r"\bdrop\s+table\b", command, re.IGNORECASE):
        return "DROP TABLE"
    if re.search(r"\btruncate\b", command, re.IGNORECASE):
        return "TRUNCATE"
    if _has_delete_without_where(command):
        return "DELETE FROM without a WHERE clause"
    return None


def _write_log(log_path: Path, payload: dict[str, Any], command: str, reason: str) -> None:
    """Append an auditable, single-line record without making the hook fail open."""

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "command": command,
            "project_path": payload.get("cwd") or payload.get("project_path") or os.getcwd(),
        }
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        # A logging failure must never allow a dangerous command through.
        pass


def process_event(payload: dict[str, Any], log_path: Path = LOG_PATH) -> dict[str, Any] | None:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return None

    reason = detect_block_reason(command)
    if reason is None:
        return None

    _write_log(log_path, payload, command, reason)
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked potentially destructive Bash command: {reason}. "
                "Review the command and run it only after making the destructive intent explicit."
            ),
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    if not isinstance(payload, dict):
        return 0

    decision = process_event(payload)
    if decision is not None:
        print(json.dumps(decision, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
