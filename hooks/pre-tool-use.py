#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive Bash commands."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys


RM_RF = re.compile(r"\brm\s+(?:-[^\s;&|]*r[^\s;&|]*f[^\s;&|]*|-[^\s;&|]*f[^\s;&|]*r[^\s;&|]*|-r\s+-f|-f\s+-r)(?:\s|$)", re.IGNORECASE)
DROP_TABLE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
GIT_FORCE_PUSH = re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)(?:\s|$)", re.IGNORECASE)
TRUNCATE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)
DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def destructive_reason(command: str) -> str | None:
    """Return a human-readable reason when *command* matches the bounty policy."""
    if RM_RF.search(command):
        return "recursive forced deletion (rm -rf)"
    if DROP_TABLE.search(command):
        return "DROP TABLE"
    if GIT_FORCE_PUSH.search(command):
        return "forced git push"
    if TRUNCATE.search(command):
        return "TRUNCATE"

    # A WHERE in another statement must not make an unsafe DELETE look safe.
    for statement in re.split(r"(?:;|\n|&&|\|\|)", command):
        match = DELETE_FROM.search(statement)
        if match and not WHERE.search(statement[match.end():]):
            return "DELETE FROM without a WHERE clause"
    return None


def log_block(command: str, project_path: str, reason: str) -> Path:
    home = Path(os.environ.get("HOME") or Path.home())
    log_path = home / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("Blocked Bash tool call: PreToolUse hook received invalid JSON input.", file=sys.stderr)
        return 2

    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        print("Blocked Bash tool call: missing tool_input object.", file=sys.stderr)
        return 2

    command = tool_input.get("command")
    if not isinstance(command, str):
        print("Blocked Bash tool call: missing command string.", file=sys.stderr)
        return 2

    reason = destructive_reason(command)
    if reason is None:
        return 0

    project_path = payload.get("cwd")
    if not isinstance(project_path, str) or not project_path:
        project_path = os.getcwd()
    log_path = log_block(command, project_path, reason)
    print(
        f"Blocked destructive Bash command: {reason}. "
        f"The command was not executed. Review {log_path} for the audit record.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
