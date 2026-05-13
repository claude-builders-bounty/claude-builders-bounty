#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCKERS = [
    ("rm -rf", re.compile(r"(^|[\s;&|])rm\s+(-[^\s]*r[^\s]*f|-?[^\s]*f[^\s]*r)\b")),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b.*\s(--force|-f|--force-with-lease)\b")),
]

DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE | re.DOTALL)
WHERE_CLAUSE = re.compile(r"\bwhere\b", re.IGNORECASE)


def extract_command(payload):
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("cmd") or "")
    return ""


def find_block_reason(command):
    for reason, pattern in BLOCKERS:
        if pattern.search(command):
            return reason

    if DELETE_FROM.search(command) and not WHERE_CLAUSE.search(command):
        return "DELETE FROM without WHERE"

    return None


def log_block(command, project_path, reason):
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(reason):
    return {
        "decision": "block",
        "reason": (
            f"Blocked dangerous Bash command: {reason}. "
            "Use a safer, reversible command or ask the user for explicit confirmation."
        ),
    }


def allow():
    return {"decision": "allow"}


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps(allow()))
        return 0

    command = extract_command(payload)
    reason = find_block_reason(command)
    if not reason:
        print(json.dumps(allow()))
        return 0

    project_path = payload.get("cwd") or payload.get("project_path") or os.getcwd()
    log_block(command, project_path, reason)
    print(json.dumps(deny(reason)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
