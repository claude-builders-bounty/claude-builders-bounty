#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code pre-tool-use hook to block destructive bash commands.
Intended install path: ~/.claude/hooks/pre-tool-use
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


BLOCK_PATTERNS = [
    (re.compile(r"\brm\s+-rf\b", re.IGNORECASE), "Blocked pattern: rm -rf"),
    (re.compile(r"\bdrop\s+table\b", re.IGNORECASE), "Blocked pattern: DROP TABLE"),
    (re.compile(r"\bgit\s+push\b[^\n]*\s--force(\b|$)", re.IGNORECASE), "Blocked pattern: git push --force"),
    (re.compile(r"\btruncate\b", re.IGNORECASE), "Blocked pattern: TRUNCATE"),
]

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def read_payload() -> Dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        return {"raw_input": raw}
    return {}


def extract_command(payload: Dict[str, Any]) -> str:
    candidates = [
        payload.get("command"),
        payload.get("input"),
        payload.get("raw_input"),
        (payload.get("tool_input") or {}).get("command") if isinstance(payload.get("tool_input"), dict) else None,
        (payload.get("tool_input") or {}).get("cmd") if isinstance(payload.get("tool_input"), dict) else None,
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    # Fallback: stringify payload for defensive matching
    try:
        return json.dumps(payload, ensure_ascii=False)
    except Exception:
        return str(payload)


def extract_project_path(payload: Dict[str, Any]) -> str:
    for key in ("project_path", "cwd", "working_directory"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return os.getcwd()


def should_block(command: str) -> str | None:
    for regex, reason in BLOCK_PATTERNS:
        if regex.search(command):
            return reason

    # Block DELETE FROM without WHERE clause
    if DELETE_FROM_RE.search(command) and not WHERE_RE.search(command):
        return "Blocked pattern: DELETE FROM without WHERE clause"

    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"

    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts}\t{project_path}\t{reason}\t{command}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    payload = read_payload()
    command = extract_command(payload)
    project_path = extract_project_path(payload)

    reason = should_block(command)
    if reason:
        log_blocked(command=command, project_path=project_path, reason=reason)
        # Clear human message for Claude Code
        print(
            "Blocked destructive command.\n"
            f"Reason: {reason}\n"
            "This action was logged to ~/.claude/hooks/blocked.log.\n"
            "Use a safer alternative or add explicit safeguards."
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
