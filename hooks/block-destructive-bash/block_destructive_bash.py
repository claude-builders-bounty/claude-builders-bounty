#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks dangerous Bash commands.

Install as a Claude Code hook for the Bash tool. The hook accepts Claude Code's
JSON event on stdin, inspects the attempted shell command, and exits non-zero
with a clear error when a destructive pattern is detected.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCK_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(r"(^|[;&|()\s])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])(?:\s|=|$)"),
        "recursive forced removal can irreversibly delete files",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE can destroy database schema/data",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)", re.IGNORECASE),
        "force-pushing can overwrite remote history",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
        "TRUNCATE can delete all rows from a table",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b)[^;\n])*($|;)", re.IGNORECASE),
        "DELETE FROM without a WHERE clause can delete every row",
    ),
]


def _extract_command(payload: dict[str, Any]) -> str:
    # Claude Code hook payloads commonly include tool_input.command for Bash.
    for path in (("tool_input", "command"), ("tool_input", "input"), ("command",), ("input",)):
        node: Any = payload
        for key in path:
            if not isinstance(node, dict) or key not in node:
                break
            node = node[key]
        else:
            if isinstance(node, str):
                return node
    return ""


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "transcript_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def _log_blocked(log_path: Path, command: str, project_path: str, rule: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_project = project_path.replace("\n", " ")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp}\trule={rule}\tproject={safe_project}\tcommand={safe_command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Blocked hook could not parse Claude Code event JSON: {exc}", file=sys.stderr)
        return 2

    command = _extract_command(payload)
    project = _project_path(payload)
    log_path = Path(os.environ.get("CLAUDE_BLOCKED_LOG", "~/.claude/hooks/blocked.log")).expanduser()

    for rule, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            _log_blocked(log_path, command, project, rule)
            print(
                f"Claude Code blocked this Bash command: {rule}. Reason: {reason}. "
                f"If this is intentional, ask the user for explicit approval and run it manually.",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
