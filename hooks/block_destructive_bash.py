#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def _delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command, flags=re.IGNORECASE):
        if re.search(r"\bDELETE\s+FROM\b", statement, flags=re.IGNORECASE):
            if not re.search(r"\bWHERE\b", statement, flags=re.IGNORECASE):
                return True
    return False


def block_reason(command: str) -> str | None:
    normalized = _normalize_command(command)

    checks = [
        (r"\brm\s+(-[A-Za-z]*r[A-Za-z]*f|-+[A-Za-z]*f[A-Za-z]*r)\b", "rm -rf can recursively and forcibly delete files"),
        (r"\bDROP\s+TABLE\b", "DROP TABLE can permanently remove database tables"),
        (r"\bgit\s+push\b[^\n;]*\s--force(?:\s|$)", "git push --force can rewrite shared history"),
        (r"\bTRUNCATE\b", "TRUNCATE can permanently remove table data"),
    ]

    for pattern, reason in checks:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return reason

    if _delete_without_where(normalized):
        return "DELETE FROM without a WHERE clause can remove every row in a table"

    return None


def project_path(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("cwd"),
        payload.get("project_path"),
        payload.get("workspace"),
        payload.get("transcript_path"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return os.getcwd()


def log_blocked(command: str, path: str, reason: str) -> None:
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with BLOCK_LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp": timestamp,
                    "command": command,
                    "project_path": path,
                    "reason": reason,
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Unable to parse Claude Code hook input: {exc}", file=sys.stderr)
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    path = project_path(payload)
    log_blocked(command, path, reason)
    print(
        "Blocked destructive Bash command before execution. "
        f"Reason: {reason}. "
        "Choose a safer command or ask the user for explicit confirmation.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
