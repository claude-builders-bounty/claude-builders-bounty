#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCK_RULES = [
    (re.compile(r"\brm\s+(?:-[A-Za-z]*[rf][A-Za-z]*\s+){0,3}[^\n;&|]*", re.I), "rm -rf style deletion"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE"),
    (re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)", re.I), "git push --force"),
    (re.compile(r"\bTRUNCATE\b", re.I), "TRUNCATE"),
    (re.compile(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", re.I), "DELETE FROM without WHERE"),
]


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    return ""


def project_path(payload: dict) -> str:
    for key in ("cwd", "project_path", "workspace", "repo"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def log_block(command: str, path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": timestamp,
            "command": command,
            "project_path": path,
            "reason": reason,
        }, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") not in ("Bash", "bash"):
        return 0

    command = extract_command(payload)
    for pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            path = project_path(payload)
            log_block(command, path, reason)
            print(f"Blocked unsafe bash command: {reason}. Review it manually or use a safer alternative.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
