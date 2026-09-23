#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks dangerous bash commands.

Reads the hook payload JSON from stdin, inspects bash/shell command text, logs
blocked attempts, and exits non-zero with a clear explanation when a dangerous
pattern is detected.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCK_PATTERNS = (
    ("rm -rf", re.compile(r"(^|[;&|()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|- [^\n]*|-[A-Za-z]*f[A-Za-z]*r)\b", re.IGNORECASE)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force|-f|--force-with-lease)\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.IGNORECASE)),
)


def extract_command(payload: dict[str, Any]) -> str:
    """Extract a shell command from common Claude Code hook payload shapes."""
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    for container in (tool_input, payload):
        for key in ("command", "cmd", "input"):
            value = container.get(key)
            if isinstance(value, str):
                return value
    return ""


def find_block_reason(command: str) -> str | None:
    for label, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return label
    return None


def log_block(reason: str, command: str, project_path: str) -> Path:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{project_path}\t{reason}\t{safe_command}\n")
    return log_path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("pre_tool_use_guard: invalid hook JSON payload", file=sys.stderr)
        return 2

    command = extract_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    project_path = os.getcwd()
    log_path = log_block(reason, command, project_path)
    print(
        f"Blocked dangerous bash command: {reason}. "
        f"The attempt was logged to {log_path}. Rewrite the command safely before continuing.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
