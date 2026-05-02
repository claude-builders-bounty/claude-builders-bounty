#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

BLOCK_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("rm -rf", re.compile(r"(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-\w*f\w*r)\b", re.IGNORECASE), "Recursive forced deletion can remove large parts of the filesystem."),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "Dropping database tables is destructive and must be reviewed manually."),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\s|=|$)|\bgit\s+push\b[^\n;|&]*\s-f(?:\s|$)", re.IGNORECASE), "Force-pushing can rewrite shared Git history."),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE removes table data without per-row safeguards."),
    ("DELETE FROM without WHERE", re.compile(r"\bDELETE\s+FROM\s+[\w.\"`]+(?:(?!\bWHERE\b)[^;])*($|;)", re.IGNORECASE | re.DOTALL), "DELETE FROM without a WHERE clause can delete every row."),
]

def _load_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {"tool_name": "Bash", "tool_input": {"command": raw}}

def _extract_command(payload: dict[str, Any]) -> str:
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    if tool_name and tool_name.lower() not in {"bash", "shell"}:
        return ""
    return command if isinstance(command, str) else ""

def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "root"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd") or tool_input.get("workdir")
        if isinstance(value, str) and value:
            return value
    return os.getcwd()

def _log_block(command: str, project_path: str, matches: list[tuple[str, str]]) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    reasons = ", ".join(name for name, _ in matches)
    safe_command = command.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"{ts}\tproject={project_path}\treasons={reasons}\tcommand={safe_command}\n")

def main() -> int:
    payload = _load_payload()
    command = _extract_command(payload)
    if not command:
        return 0
    matches = [(name, message) for name, pattern, message in BLOCK_PATTERNS if pattern.search(command)]
    if not matches:
        return 0
    project_path = _project_path(payload)
    _log_block(command, project_path, matches)
    print("Claude Code pre-tool-use hook blocked a destructive Bash command.", file=sys.stderr)
    for name, message in matches:
        print(f"- {name}: {message}", file=sys.stderr)
    print("Review the command manually before running it outside Claude Code.", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
