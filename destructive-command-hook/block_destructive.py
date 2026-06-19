#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCK_PATTERNS = [
    ("rm -rf", re.compile(r"(^|[;&|]\s*)rm\s+-(?:[^\s-]*r[^\s-]*f|[^\s-]*f[^\s-]*r)\b")),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;|&]*(?:--force|-f)\b")),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b|;).)*($|;)", re.IGNORECASE | re.DOTALL)),
]


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("cmd") or "")
    return ""


def find_block_reason(command: str) -> str | None:
    for reason, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp}\t{project_path}\t{reason}\t{command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    command = extract_command(payload)
    project_path = str(payload.get("cwd") or payload.get("project_path") or os.getcwd())
    reason = find_block_reason(command)
    if not reason:
        return 0

    log_block(command, project_path, reason)
    print(
        f"Blocked destructive command: {reason}. Use a safer command or ask for explicit approval.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
