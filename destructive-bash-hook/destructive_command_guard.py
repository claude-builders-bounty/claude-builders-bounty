#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Designed for Claude Code's PreToolUse hook lifecycle. The hook reads the tool
payload from stdin when available, falls back to CLAUDE_TOOL_INPUT, and exits:
- 0 when the command is allowed
- 2 when the command is blocked so Claude Code treats the hook as a gate
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

DANGEROUS_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "recursive force delete",
        re.compile(r"(?:^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)(?:\s|$)"),
        "`rm -rf` can permanently delete files. Use a targeted delete or ask the user for approval.",
    ),
    (
        "drop table",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "`DROP TABLE` is destructive database DDL. Require explicit human approval and a backup plan.",
    ),
    (
        "force push",
        re.compile(r"\bgit\s+push\b[^\n;|&]*\s(?:--force(?:-with-lease)?|-f)\b", re.IGNORECASE),
        "Force-pushing can rewrite shared history. Use a normal push or ask the user for approval.",
    ),
    (
        "truncate",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "`TRUNCATE` can erase table data. Require explicit human approval and a backup plan.",
    ),
    (
        "delete without where",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b).)*(?:;|$)", re.IGNORECASE | re.DOTALL),
        "`DELETE FROM` without a `WHERE` clause can erase an entire table.",
    ),
]


def _load_json(value: str) -> dict[str, Any]:
    if not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def read_payload() -> dict[str, Any]:
    """Read Claude hook payload from stdin, then env fallback."""
    stdin_text = ""
    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read()
    payload = _load_json(stdin_text)
    if payload:
        return payload

    env_payload = os.environ.get("CLAUDE_TOOL_INPUT", "")
    payload = _load_json(env_payload)
    if payload:
        return payload

    # Last fallback: allow simple direct testing with COMMAND env var.
    command = os.environ.get("COMMAND", "")
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def extract_command(payload: dict[str, Any]) -> str:
    """Extract a Bash command from known Claude Code hook payload shapes."""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd")
        if isinstance(command, str):
            return command

    direct_command = payload.get("command") or payload.get("cmd")
    if isinstance(direct_command, str):
        return direct_command

    # Some hook setups expose CLAUDE_TOOL_INPUT as raw JSON command payload.
    env_payload = _load_json(os.environ.get("CLAUDE_TOOL_INPUT", ""))
    env_command = env_payload.get("command") if isinstance(env_payload, dict) else None
    return env_command if isinstance(env_command, str) else ""


def find_block_reason(command: str) -> tuple[str, str] | None:
    """Return (pattern_name, explanation) when command should be blocked."""
    for name, pattern, explanation in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return name, explanation
    return None


def project_path(payload: dict[str, Any]) -> str:
    candidate = (
        os.environ.get("CLAUDE_PROJECT_DIR")
        or payload.get("cwd")
        or payload.get("project_dir")
        or payload.get("projectPath")
        or os.getcwd()
    )
    return str(candidate)


def write_block_log(command: str, project: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sanitized = command.replace("\n", "\\n")
    with BLOCKED_LOG.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp}\tproject={project}\treason={reason}\tcommand={sanitized}\n")


def main() -> int:
    payload = read_payload()
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "Bash")

    # Only gate Bash invocations; stay silent for other tools.
    if tool_name.lower() not in {"bash", "bashtool"}:
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    block = find_block_reason(command)
    if not block:
        return 0

    reason, explanation = block
    project = project_path(payload)
    write_block_log(command, project, reason)

    print(
        "Blocked destructive Bash command before execution.\n"
        f"Reason: {explanation}\n"
        f"Project: {project}\n"
        f"Log: {BLOCKED_LOG}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
