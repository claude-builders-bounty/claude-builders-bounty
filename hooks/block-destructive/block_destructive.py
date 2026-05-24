#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCKED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+(-[^\s]*\s+)*-[^\s]*r[^\s]*f|\brm\s+-rf\b", re.I), "`rm -rf` deletes files irreversibly"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "`DROP TABLE` can destroy database tables"),
    (re.compile(r"\bgit\s+push\b[^\n]*--force\b|\bgit\s+push\s+-f\b", re.I), "`git push --force` can overwrite remote history"),
    (re.compile(r"\bTRUNCATE\b", re.I), "`TRUNCATE` removes all rows from a table"),
    (
        re.compile(r"\bDELETE\s+FROM\b(?:(?!WHERE).)*$", re.I | re.S),
        "`DELETE FROM` without a WHERE clause can wipe an entire table",
    ),
]


def extract_bash_command(payload: dict) -> str | None:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, str):
        return tool_input
    if not isinstance(tool_input, dict):
        return None
    if payload.get("tool_name") not in (None, "Bash", "bash"):
        return None
    cmd = tool_input.get("command") or tool_input.get("cmd")
    return str(cmd) if cmd else None


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    command = extract_bash_command(payload)
    if not command:
        return 0

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            project = payload.get("cwd") or payload.get("project_path") or payload.get("workspace") or "unknown"
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).isoformat()
            LOG_PATH.open("a", encoding="utf-8").write(
                f"{ts}\tproject={project}\tcommand={command!r}\treason={reason}\n"
            )
            print(
                f"Blocked destructive command: {reason}. "
                f"Command was not executed. Logged to {LOG_PATH}.",
                file=sys.stderr,
            )
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
