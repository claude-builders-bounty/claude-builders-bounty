#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive bash commands.

The hook reads JSON from stdin, extracts the attempted bash command, and exits:
- 0 for allowed commands
- 2 for blocked commands
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def _get_nested(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_command(payload: dict[str, Any]) -> str:
    """Extract command from common Claude Code hook payload shapes."""
    candidates = [
        ("tool_input", "command"),
        ("tool_input", "cmd"),
        ("input", "command"),
        ("input", "cmd"),
        ("command",),
        ("cmd",),
    ]

    for path in candidates:
        value = _get_nested(payload, path)
        if isinstance(value, str) and value.strip():
            return value

    return ""


def delete_without_where(command: str) -> bool:
    """Detect DELETE FROM statements that do not include a WHERE clause."""
    normalized = re.sub(r"\s+", " ", command.strip(), flags=re.MULTILINE).lower()
    match = re.search(r"\bdelete\s+from\b", normalized)
    if not match:
        return False

    # Only inspect the first SQL statement after DELETE FROM.
    statement = normalized[match.start() :].split(";", 1)[0]
    return " where " not in f" {statement} "


def blocked_reason(command: str) -> str | None:
    checks: list[tuple[str, str]] = [
        (r"\brm\s+(-[^\n;]*[rf][^\n;]*|-[^\n;]*[fr][^\n;]*)\b", "rm -rf style recursive force deletion"),
        (r"\bdrop\s+table\b", "DROP TABLE statement"),
        (r"\btruncate\b", "TRUNCATE statement"),
        (r"\bgit\s+push\b[^\n;]*(--force|-f)\b", "force-pushing with git push"),
    ]

    for pattern, reason in checks:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return reason

    if delete_without_where(command):
        return "DELETE FROM statement without a WHERE clause"

    return None


def log_block(command: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    safe_command = command.replace("\n", "\\n")
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{timestamp}\tproject={project_path}\treason={reason}\tcommand={safe_command}\n"
        )


def main() -> int:
    raw_input = sys.stdin.read()
    try:
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    command = extract_command(payload)
    reason = blocked_reason(command)

    if not reason:
        return 0

    log_block(command, reason)
    print(
        "Blocked destructive bash command before execution.\n"
        f"Reason: {reason}.\n"
        "If this operation is genuinely required, perform it manually after review.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
