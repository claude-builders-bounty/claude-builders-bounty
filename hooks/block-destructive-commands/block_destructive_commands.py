#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


DENY_RESPONSE = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "",
    }
}


def normalize_sql(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip(), flags=re.MULTILINE).lower()


def destructive_reason(command: str) -> str | None:
    shell = command.lower()
    sql = normalize_sql(command)

    if re.search(r"(^|[;&|]\s*)rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b", shell):
        return "rm -rf"

    if re.search(r"\bgit\s+push\b[^;&|]*\s(--force|-f)\b", shell):
        return "git push --force"

    if re.search(r"\bdrop\s+table\b", sql):
        return "DROP TABLE"

    if re.search(r"\btruncate\b", sql):
        return "TRUNCATE"

    for statement in re.split(r";|&&|\|\|", sql):
        if re.search(r"\bdelete\s+from\b", statement) and not re.search(r"\bwhere\b", statement):
            return "DELETE FROM without WHERE"

    return None


def project_path(payload: dict) -> str:
    return (
        str(payload.get("cwd") or "")
        or str(payload.get("workspace") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
        or os.getcwd()
    )


def log_block(command: str, project: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "project_path": project,
            "reason": reason,
            "command": command,
        },
        ensure_ascii=False,
    )
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = destructive_reason(command)
    if reason is None:
        return 0

    project = project_path(payload)
    log_block(command, project, reason)

    response = DENY_RESPONSE.copy()
    response["hookSpecificOutput"] = DENY_RESPONSE["hookSpecificOutput"].copy()
    response["hookSpecificOutput"][
        "permissionDecisionReason"
    ] = f"Blocked destructive Bash command: {reason}. Review the command and use a safer, scoped alternative."
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
