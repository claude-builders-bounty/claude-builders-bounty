#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads Claude Code hook JSON from stdin. When a dangerous Bash command
is detected, it logs the attempt and returns a PreToolUse deny decision.
Normal commands exit silently with status 0 so the default permission flow is
not changed.
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


def _compact(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def _rm_rf(command: str) -> bool:
    """Detect rm invocations that combine recursive and force flags."""
    for match in re.finditer(r"(?:^|[;&|]\s*)rm\s+((?:-[A-Za-z]+\s*)+)", command):
        flags = match.group(1)
        flag_chars = "".join(re.findall(r"-([A-Za-z]+)", flags))
        if "r" in flag_chars and "f" in flag_chars:
            return True
    return False


def _git_push_force(command: str) -> bool:
    return bool(re.search(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\b|=|-with-lease\b)", command, re.IGNORECASE))


def _delete_from_without_where(command: str) -> bool:
    """Block any DELETE FROM statement segment that does not contain WHERE."""
    for statement in re.split(r";", command):
        if re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, re.IGNORECASE
        ):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    checks = [
        (_rm_rf, "rm -rf recursively deletes files without confirmation"),
        (lambda value: bool(re.search(r"\bdrop\s+table\b", value, re.IGNORECASE)), "DROP TABLE can destroy database schema/data"),
        (_git_push_force, "git push --force can overwrite remote history"),
        (lambda value: bool(re.search(r"\btruncate\b", value, re.IGNORECASE)), "TRUNCATE can irreversibly remove table data"),
        (_delete_from_without_where, "DELETE FROM without WHERE can delete every row in a table"),
    ]
    for predicate, reason in checks:
        if predicate(command):
            return reason
    return None


def _project_path(payload: dict[str, Any]) -> str:
    return str(
        payload.get("cwd")
        or payload.get("project_dir")
        or payload.get("workspace")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Destructive command blocked: {reason}. Ask the user before attempting a safer alternative.",
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Invalid hook payload should not block unrelated work.
        return 0

    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name != "Bash":
        return 0

    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(tool_input, dict):
        return 0

    command = str(tool_input.get("command") or "")
    if not command.strip():
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    log_blocked_attempt(_compact(command), project_path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
