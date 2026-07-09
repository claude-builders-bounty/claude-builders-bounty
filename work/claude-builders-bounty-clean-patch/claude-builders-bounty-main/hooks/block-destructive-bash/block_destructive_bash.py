#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple


class BlockMatch(NamedTuple):
    pattern: str
    reason: str


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b(?P<body>[^;]*)", re.IGNORECASE)
GIT_PUSH_FORCE_RE = re.compile(
    r"(?:^|[;&|()\s])git\s+push\b(?=[^;&|]*?(?:--force(?:-with-lease)?\b|-f\b))",
    re.IGNORECASE,
)
RM_FORCE_RECURSIVE_RE = re.compile(
    r"(?:^|[;&|()\s])(?:sudo\s+)?rm\s+(?:(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*)|(?:-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)|(?:(?:--recursive|-r|-R)\s+(?:--force|-f))|(?:(?:--force|-f)\s+(?:--recursive|-r|-R)))\b",
    re.IGNORECASE,
)


def blocked_log_path() -> Path:
    configured = os.environ.get("CLAUDE_BLOCKED_LOG")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def find_blocked_pattern(command: str) -> BlockMatch | None:
    """Return the destructive pattern matched by a Bash command, if any."""
    if RM_FORCE_RECURSIVE_RE.search(command):
        return BlockMatch("rm -rf", "Recursive forced removal can delete project or system files.")

    if GIT_PUSH_FORCE_RE.search(command):
        return BlockMatch("git push --force", "Force-pushing can rewrite shared repository history.")

    if DROP_TABLE_RE.search(command):
        return BlockMatch("DROP TABLE", "DROP TABLE permanently removes database tables.")

    if TRUNCATE_RE.search(command):
        return BlockMatch("TRUNCATE", "TRUNCATE can irreversibly remove table data.")

    for match in DELETE_FROM_RE.finditer(command):
        statement_tail = match.group("body")
        if not re.search(r"\bwhere\b", statement_tail, re.IGNORECASE):
            return BlockMatch(
                "DELETE FROM without WHERE",
                "DELETE FROM without a WHERE clause can remove every row in a table.",
            )

    return None


def project_path_from_payload(payload: dict[str, Any]) -> str:
    """Best-effort project path extraction across Claude Code hook payload versions."""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cwd", "project_path", "working_directory"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value

    for key in ("cwd", "project_path", "workspace", "workspace_path"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def append_block_log(command: str, project_path: str, match: BlockMatch, log_path: Path | None = None) -> None:
    if log_path is None:
        log_path = blocked_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "blocked_pattern": match.pattern,
        "reason": match.reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def denial_payload(match: BlockMatch) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command ({match.pattern}): {match.reason} "
                "Revise the command to use a safer, scoped alternative."
            ),
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command.strip():
        return 0

    match = find_blocked_pattern(command)
    if match is None:
        return 0

    try:
        append_block_log(command, project_path_from_payload(payload), match)
    except OSError:
        pass
    print(json.dumps(denial_payload(match)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())