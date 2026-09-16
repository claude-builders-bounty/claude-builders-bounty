#!/usr/bin/env python3
"""A Claude Code PreToolUse hook that rejects destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("`rm -rf` can recursively and permanently delete files", re.compile(r"(?:^|[;&|]\s*)rm\s+(?:[^\n;&|]*\s)?-[A-Za-z]*r[A-Za-z]*f|(?:^|[;&|]\s*)rm\s+(?:[^\n;&|]*\s)?-[A-Za-z]*f[A-Za-z]*r", re.IGNORECASE)),
    ("`DROP TABLE` permanently removes a database table", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("`git push --force` can overwrite remote history", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b|\bgit\s+push\b[^\n;&|]*\s-f\b", re.IGNORECASE)),
    ("`TRUNCATE` permanently removes all rows from a table", re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)),
)


def has_unsafe_delete(command: str) -> bool:
    """Return true only for DELETE FROM statements without a WHERE clause."""
    for statement in re.split(r";", command):
        if re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, re.IGNORECASE
        ):
            return True
    return False


def reason_for(command: str) -> str | None:
    for reason, pattern in RULES:
        if pattern.search(command):
            return reason
    if has_unsafe_delete(command):
        return "`DELETE FROM` without `WHERE` can remove every row in a table"
    return None


def log_block(command: str, project_path: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = reason_for(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    log_block(command, project_path)
    print(f"Blocked destructive Bash command: {reason}. Use a scoped, reversible alternative.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
