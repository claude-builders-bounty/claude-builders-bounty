#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCKED_PATTERNS = [
    ("rm -rf", re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b|\brm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b")),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
]


def delete_without_where(command):
    for match in re.finditer(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
        statement = command[match.start():]
        statement = re.split(r"[;\n]", statement, maxsplit=1)[0]
        if not re.search(r"\bWHERE\b", statement, re.IGNORECASE):
            return True
    return False


def block_reason(command):
    for label, pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return label
    if delete_without_where(command):
        return "DELETE FROM without WHERE"
    return None


def log_blocked(command, project_path, reason):
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as log:
        log.write(f"{timestamp}\t{project_path}\t{reason}\t{command}\n")


def main():
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Bash":
        return

    command = payload.get("tool_input", {}).get("command", "")
    reason = block_reason(command)
    if not reason:
        return

    project_path = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_blocked(command, project_path, reason)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command: {reason}"
        }
    }))


if __name__ == "__main__":
    main()
