#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads Claude Code hook JSON from stdin. If the event is a Bash tool call and
its command matches one of the configured destructive patterns, the hook logs
the attempt and returns a PreToolUse deny decision.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

RM_RF_RE = re.compile(
    r"(?:^|[;&|()\s])rm\s+(?:-(?=[A-Za-z]*r)(?=[A-Za-z]*f)[A-Za-z]+|-[A-Za-z]*r[A-Za-z]*\s+-[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*\s+-[A-Za-z]*r[A-Za-z]*)(?:\s|$)",
    re.IGNORECASE,
)
DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
FORCE_PUSH_RE = re.compile(r"\bgit\s+push\b[^\n;]*?(?:--force(?:-with-lease)?\b|\s-f\b)", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def _split_sql_statements(command: str) -> Iterable[str]:
    """Return coarse SQL-ish statements split on semicolons and newlines."""
    for part in re.split(r";|\n", command):
        part = part.strip()
        if part:
            yield part


def find_block_reason(command: str) -> Optional[str]:
    """Return a human-readable block reason if the command is dangerous."""
    if RM_RF_RE.search(command):
        return "Blocked destructive recursive force removal (`rm -rf`/`rm -fr`)."
    if FORCE_PUSH_RE.search(command):
        return "Blocked force push (`git push --force`, `--force-with-lease`, or `-f`)."
    if DROP_TABLE_RE.search(command):
        return "Blocked destructive SQL schema operation (`DROP TABLE`)."
    if TRUNCATE_RE.search(command):
        return "Blocked destructive SQL data operation (`TRUNCATE`)."
    for statement in _split_sql_statements(command):
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return "Blocked `DELETE FROM` without a `WHERE` clause."
    return None


def project_path(payload: Dict[str, Any]) -> str:
    return (
        payload.get("cwd")
        or payload.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def log_block(command: str, reason: str, project: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project,
        "attempted_command": command,
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
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid Claude Code hook JSON: {exc}", file=sys.stderr)
        return 1

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = find_block_reason(command)
    if not reason:
        return 0

    project = project_path(payload)
    log_block(command, reason, project)
    deny(f"{reason} Command was not executed. Project: {project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
