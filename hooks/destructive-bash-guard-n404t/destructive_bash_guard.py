#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive Bash commands."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

RULES: list[tuple[str, re.Pattern[str]]] = [
    ("rm -rf", re.compile(r"(^|[;&|()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-[A-Za-z]*f[A-Za-z]*r)\b")),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force|-f|--force-with-lease)\b")),
    ("DELETE FROM without WHERE", re.compile(r"\bDELETE\s+FROM\s+[^;\n]+(?:;|$)", re.IGNORECASE)),
]

WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("script") or "")
    return ""


def _blocked_reason(command: str) -> str | None:
    for name, pattern in RULES:
        match = pattern.search(command)
        if not match:
            continue
        if name == "DELETE FROM without WHERE" and WHERE_RE.search(match.group(0)):
            continue
        return name
    return None


def _log(reason: str, command: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    project = os.getcwd()
    safe_command = command.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"{now}\t{project}\t{reason}\t{safe_command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("destructive-bash-guard: invalid hook JSON", file=sys.stderr)
        return 0

    if payload.get("tool_name") not in (None, "Bash"):
        return 0

    command = _extract_command(payload)
    reason = _blocked_reason(command)
    if not reason:
        return 0

    _log(reason, command)
    print(
        f"Blocked destructive Bash command: {reason}. "
        f"Attempt logged to {LOG_PATH}. Rewrite command to avoid destructive action.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
