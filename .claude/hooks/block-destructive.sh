#!/usr/bin/env python3
"""Block a small, explicit set of destructive Bash commands for Claude Code."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def read_input() -> dict:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def command_from(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def project_path_from(payload: dict) -> str:
    for key in ("cwd", "project_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def blocked_reason(command: str) -> str | None:
    if re.search(r"\brm\s+(?:(?:-[a-zA-Z]*[rf][a-zA-Z]*\b)|(?:--force\b.*--recursive\b)|(?:--recursive\b.*--force\b))", command):
        return "rm -rf is blocked because it can recursively and forcibly delete data."
    if re.search(r"\bDROP\s+TABLE\b", command, re.IGNORECASE):
        return "DROP TABLE is blocked because it can irreversibly remove a database table."
    if re.search(r"\bgit\s+push\b[^\n]*(?:--force\b|-f\b)", command, re.IGNORECASE):
        return "Forced git push is blocked because it can overwrite remote history."
    if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", command, re.IGNORECASE):
        return "TRUNCATE is blocked because it can irreversibly remove table data."
    delete_match = re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE)
    if delete_match and not re.search(r"\bWHERE\b", command[delete_match.end():], re.IGNORECASE):
        return "DELETE FROM without WHERE is blocked because it can remove every row."
    return None


def append_log(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = read_input()
    command = command_from(payload)
    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = project_path_from(payload)
    try:
        append_log(command, project_path, reason)
    except OSError as error:
        print(f"Unable to write blocked command log: {error}", file=sys.stderr)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
            "additionalContext": (
                "The command was blocked by the destructive-command safety hook. "
                "Explain the risk and ask for a safer, narrower command if appropriate."
            ),
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
