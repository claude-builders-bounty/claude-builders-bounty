#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands.

Reads the Claude hook payload from stdin as JSON. If the tool call is Bash and
its command matches a destructive pattern, the hook logs the blocked attempt and
exits non-zero with a clear explanation. Normal commands exit 0.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("recursive forced removal", re.compile(r"\brm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF][A-Za-z]*|-[A-Za-z]*[fF][A-Za-z]*[rR][A-Za-z]*)\b")),
    ("DROP TABLE statement", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("forced git push", re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:-with-lease)?\b", re.IGNORECASE)),
    ("TRUNCATE statement", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b).)*(?:$|;)", re.IGNORECASE | re.DOTALL)),
]


def extract_command(payload: dict) -> str:
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = str(tool_input.get("command") or tool_input.get("cmd") or "")
    if tool_name and tool_name.lower() not in {"bash", "shell"}:
        return ""
    return command


def blocked_reason(command: str) -> str | None:
    for reason, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def log_block(command: str, project_path: str, reason: str) -> Path:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_project = project_path.replace("\n", " ")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"{timestamp}\t{safe_project}\t{reason}\t{safe_command}\n")
    return log_path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Safety hook could not parse JSON payload: {exc}", file=sys.stderr)
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = str(
        payload.get("cwd")
        or payload.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    log_path = log_block(command, project_path, reason)
    print(
        "Blocked by pre-tool-use safety hook: "
        f"{reason}. The attempted command was logged to {log_path}. "
        "Review it manually before running anything destructive.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
