#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def _extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    return ""


def _project_path(payload: dict) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def _blocked_reason(command: str) -> str | None:
    checks = [
        (r"\brm\s+-[^\n;|&]*r[^\n;|&]*f|\brm\s+-[^\n;|&]*f[^\n;|&]*r", "rm -rf can recursively delete files"),
        (r"\bDROP\s+TABLE\b", "DROP TABLE can destroy database schema/data"),
        (r"\bgit\s+push\b[^\n;|&]*\s--force(?:\s|$)", "git push --force can rewrite shared history"),
        (r"\bTRUNCATE\b", "TRUNCATE can delete all rows from a table"),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command, re.IGNORECASE):
            return reason

    for match in re.finditer(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
        tail = command[match.end():]
        statement = re.split(r"[;\n]", tail, maxsplit=1)[0]
        if not re.search(r"\bWHERE\b", statement, re.IGNORECASE):
            return "DELETE FROM without WHERE can delete every matching row"
    return None


def _log_block(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    with BLOCKED_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "timestamp": timestamp,
            "command": command,
            "project_path": project_path,
            "reason": reason,
        }, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Hook input was not valid JSON: {exc}", file=sys.stderr)
        return 0

    command = _extract_command(payload)
    reason = _blocked_reason(command)
    if not reason:
        return 0

    project_path = _project_path(payload)
    _log_block(command, project_path, reason)
    print(
        "Blocked destructive bash command.\n"
        f"Reason: {reason}.\n"
        f"Project: {project_path}.\n"
        f"Attempt logged to {BLOCKED_LOG}.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
