#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"(?is)(^|[;&|]\s*)rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|- [^\n]*\br\b[^\n]*\bf\b)"),
        "Recursive forced removal is blocked. Review the target path and delete manually if it is intentional.",
    ),
    (
        "DROP TABLE",
        re.compile(r"(?is)\bdrop\s+table\b"),
        "DROP TABLE is blocked because it can destroy schema and data.",
    ),
    (
        "git push --force",
        re.compile(r"(?is)\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b"),
        "Force-pushing is blocked. Use a reviewed non-force push or explicitly coordinate branch replacement.",
    ),
    (
        "TRUNCATE",
        re.compile(r"(?is)\btruncate\b"),
        "TRUNCATE is blocked because it removes table data without row-level filtering.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"(?is)\bdelete\s+from\b(?:(?!\bwhere\b|[;\n]).)*($|[;\n])"),
        "DELETE FROM without a WHERE clause is blocked.",
    ),
)


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
    else:
        command = ""
    return str(command)


def _project_path(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("cwd"),
        payload.get("project_path"),
        payload.get("workspace"),
        (payload.get("tool_input") or {}).get("cwd") if isinstance(payload.get("tool_input"), dict) else None,
        os.getcwd(),
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    return ""


def check_command(command: str) -> tuple[bool, str, str]:
    for name, pattern, message in BLOCK_RULES:
        if pattern.search(command):
            return True, name, message
    return False, "", ""


def log_blocked(command: str, project_path: str, rule_name: str) -> Path:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "project_path": project_path,
        "matched_rule": rule_name,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return log_path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps({"continue": False, "decision": "block", "reason": f"Invalid hook JSON: {exc}"}))
        return 0

    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    if tool_name and tool_name.lower() != "bash":
        print(json.dumps({"continue": True}))
        return 0

    command = _extract_command(payload)
    blocked, rule_name, message = check_command(command)
    if not blocked:
        print(json.dumps({"continue": True}))
        return 0

    project_path = _project_path(payload)
    log_path = log_blocked(command, project_path, rule_name)
    reason = f"Blocked dangerous Bash command ({rule_name}): {message} Logged to {log_path}."
    print(json.dumps({"continue": False, "decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
