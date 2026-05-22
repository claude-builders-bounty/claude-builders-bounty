#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive Bash commands."""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def hook_dir() -> Path:
    return Path.home() / ".claude" / "hooks"


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {"tool_input": {"command": raw}}


def command_from_payload(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd")
        if isinstance(command, str):
            return command
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def project_path_from_payload(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("cwd"),
        payload.get("project_path"),
        payload.get("workspace"),
    ]
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        candidates.extend([tool_input.get("cwd"), tool_input.get("workdir")])
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return os.getcwd()


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name") or payload.get("tool")
    if not tool_name:
        return True
    return str(tool_name).lower() in {"bash", "shell", "terminal"}


def delete_from_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command, flags=re.IGNORECASE):
        normalized = " ".join(statement.split()).lower()
        if normalized.startswith("delete from ") and " where " not in f" {normalized} ":
            return True
    return False


def blocked_reason(command: str) -> str | None:
    checks: list[tuple[str, str]] = [
        (r"(?i)(^|[;&|]\s*)rm\s+-(?:[^\s]*r[^\s]*f|[^\s]*f[^\s]*r)\b", "rm -rf recursively deletes files without confirmation"),
        (r"(?i)\bdrop\s+table\b", "DROP TABLE can delete database tables"),
        (r"(?i)\bgit\s+push\b[^\n;]*\s--force(?:\b|=)", "git push --force can overwrite remote history"),
        (r"(?i)\btruncate\b", "TRUNCATE can remove table data"),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command):
            return reason
    if delete_from_without_where(command):
        return "DELETE FROM without a WHERE clause can remove all rows"
    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    directory = hook_dir()
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / "blocked.log"
    is_new = not log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(["timestamp", "attempted_command", "project_path", "reason"])
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            command,
            project_path,
            reason,
        ])


def deny_response(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    payload = load_payload()
    if not is_bash_tool(payload):
        return 0

    command = command_from_payload(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    project_path = project_path_from_payload(payload)
    log_blocked(command, project_path, reason)
    message = (
        "Blocked destructive Bash command: "
        + reason
        + ". Review the command manually before proceeding."
    )
    print(json.dumps(deny_response(message), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
