#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCK_PATTERNS = [
    (re.compile(r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f|- [^\n]*?-[A-Za-z]*r[A-Za-z]*f|-[A-Za-z]*f[A-Za-z]*r)\b"), "rm -rf can permanently delete files"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE can destroy schema/data"),
    (re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\s|$|=)", re.IGNORECASE), "git push --force can overwrite remote history"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE can remove all rows from a table"),
    (re.compile(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", re.IGNORECASE), "DELETE FROM without WHERE can remove all rows"),
]


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("cmd") or tool_input.get("script") or "")
    return ""


def log_block(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": stamp, "command": command, "project_path": project_path, "reason": reason}, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    command = extract_command(payload)
    project_path = str(payload.get("cwd") or payload.get("project_path") or os.getcwd())

    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            log_block(command, project_path, reason)
            print(f"Blocked destructive command: {reason}. Review the command and ask the user for an explicit safer alternative.", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
