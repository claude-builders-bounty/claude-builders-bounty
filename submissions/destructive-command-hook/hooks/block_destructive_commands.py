#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "workspace_path"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cwd", "project_path", "workspace", "workspace_path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value

    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _shell_commands(command: str) -> Iterable[str]:
    """Split only on common shell separators; keep it intentionally simple."""
    for part in re.split(r"(?:&&|\|\||;|\n)", command):
        cleaned = part.strip()
        if cleaned:
            yield cleaned


def _delete_without_where(command: str) -> bool:
    """Detect DELETE FROM statements without a WHERE before the statement ends."""
    for match in re.finditer(r"\bDELETE\s+FROM\b", command, flags=re.IGNORECASE):
        tail = command[match.end() :]
        end = re.search(r"(?:;|&&|\|\||\n|$)", tail)
        statement = tail[: end.start()] if end else tail
        if not re.search(r"\bWHERE\b", statement, flags=re.IGNORECASE):
            return True
    return False


def _rm_force_recursive(command_part: str) -> bool:
    try:
        tokens = shlex.split(command_part, posix=True)
    except ValueError:
        tokens = command_part.split()

    if not tokens:
        return False

    index = 0
    if tokens[index] == "sudo" and len(tokens) > 1:
        index += 1

    if Path(tokens[index]).name != "rm":
        return False

    recursive = False
    force = False
    for token in tokens[index + 1 :]:
        if token == "--":
            break
        if not token.startswith("-"):
            continue
        if token == "--recursive":
            recursive = True
        elif token == "--force":
            force = True
        elif token.startswith("-") and not token.startswith("--"):
            flags = token.lstrip("-")
            recursive = recursive or "r" in flags.lower() or "R" in flags
            force = force or "f" in flags.lower()

    return recursive and force


def _block_reasons(command: str) -> list[str]:
    normalized = _compact(command)
    reasons: list[str] = []

    for part in _shell_commands(normalized):
        if _rm_force_recursive(part):
            reasons.append("recursive force deletion with rm -rf style flags")
            break

    if re.search(r"\bDROP\s+TABLE\b", normalized, flags=re.IGNORECASE):
        reasons.append("DROP TABLE statement")

    if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", normalized, flags=re.IGNORECASE):
        reasons.append("TRUNCATE statement")

    if _delete_without_where(normalized):
        reasons.append("DELETE FROM statement without a WHERE clause")

    if re.search(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)\b", normalized):
        reasons.append("force-pushing to a git remote")

    return reasons


def _log_blocked(command: str, project_path: str, reasons: list[str]) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    event = {
        "timestamp": timestamp,
        "project_path": project_path,
        "command": command,
        "reasons": reasons,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(event, ensure_ascii=False) + "\n")


def _allow() -> int:
    return 0


def _block(command: str, project_path: str, reasons: list[str]) -> int:
    _log_blocked(command, project_path, reasons)
    reason_text = "; ".join(reasons)
    message = (
        "Blocked destructive command before execution. "
        f"Reason: {reason_text}. "
        "Ask the user for explicit confirmation and suggest a safer alternative."
    )
    print(json.dumps({"decision": "block", "reason": message}, ensure_ascii=False))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return _allow()

    if not isinstance(payload, dict):
        return _allow()

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return _allow()

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return _allow()

    reasons = _block_reasons(command)
    if not reasons:
        return _allow()

    return _block(command, _project_path(payload), reasons)


if __name__ == "__main__":
    raise SystemExit(main())
