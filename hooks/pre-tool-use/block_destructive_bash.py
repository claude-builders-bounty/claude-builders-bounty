#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive Bash commands.

Input: Claude Code hook JSON payload on stdin. The script inspects Bash tool
commands and exits non-zero when the command matches a destructive pattern.
Blocked attempts are appended to ~/.claude/hooks/blocked.log as JSONL with:
timestamp, attempted command, project path, and matched rule.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RULES: list[tuple[str, re.Pattern[str]]] = [
    ("rm -rf", re.compile(r"(?i)(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-[-A-Za-z]*f[A-Za-z]*r)\b")),
    ("DROP TABLE", re.compile(r"(?is)\bdrop\s+table\b")),
    ("git push --force", re.compile(r"(?i)\bgit\s+push\b[^\n;|&]*\s--force(?:\b|=|-)")),
    ("TRUNCATE", re.compile(r"(?is)\btruncate\b")),
    ("DELETE FROM without WHERE", re.compile(r"(?is)\bdelete\s+from\s+[\w.\"`]+(?:(?!\bwhere\b).)*(?:;|$)")),
]


def _command_from_payload(payload: dict[str, Any]) -> str:
    """Extract the Bash command from common Claude Code hook payload shapes."""
    candidates = [
        payload.get("tool_input", {}).get("command"),
        payload.get("tool", {}).get("input", {}).get("command"),
        payload.get("input", {}).get("command"),
        payload.get("command"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _tool_name(payload: dict[str, Any]) -> str:
    candidates = [payload.get("tool_name"), payload.get("tool", {}).get("name"), payload.get("name")]
    for value in candidates:
        if isinstance(value, str):
            return value
    return ""


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def _matched_rule(command: str) -> str | None:
    for name, pattern in RULES:
        if pattern.search(command):
            if name == "DELETE FROM without WHERE" and re.search(r"(?is)\bdelete\s+from\s+[\w.\"`]+.*\bwhere\b", command):
                continue
            return name
    return None


def _log_block(command: str, project_path: str, rule: str) -> Path:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "rule": rule,
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return log_path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"pre-tool-use hook error: invalid JSON payload: {exc}", file=sys.stderr)
        return 0  # fail-open for malformed hook payloads so normal work is not blocked

    tool = _tool_name(payload).lower()
    command = _command_from_payload(payload)

    if tool and tool not in {"bash", "shell", "exec"}:
        return 0
    if not command:
        return 0

    rule = _matched_rule(command)
    if not rule:
        return 0

    project_path = _project_path(payload)
    log_path = _log_block(command, project_path, rule)
    print(
        "Blocked destructive bash command before execution.\n"
        f"Rule matched: {rule}\n"
        f"Project: {project_path}\n"
        f"Log: {log_path}\n"
        "Rewrite the command to a safer, narrower operation or ask the user for explicit confirmation.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
