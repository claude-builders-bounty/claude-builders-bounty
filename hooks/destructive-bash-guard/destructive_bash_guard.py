#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook is intentionally dependency-free and defensive about input shape:
Claude Code hook payloads are JSON on stdin, while older/local setups may expose
CLAUDE_TOOL_INPUT and CLAUDE_PROJECT_DIR environment variables. Both are
supported so the same file works in real hook execution and in shell tests.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class BlockReason:
    name: str
    explanation: str


# Keep these rules focused on the issue acceptance criteria while avoiding the
# most common evasion forms: whitespace variation, optional semicolons, quoted
# SQL fragments, sudo/command/env wrappers, and command substitutions.
BLOCK_RULES: tuple[tuple[re.Pattern[str], BlockReason], ...] = (
    (
        re.compile(r"(?ix)(?:^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])(?:\s|=|$)"),
        BlockReason("rm -rf", "recursive forced removal can delete project or system files"),
    ),
    (
        re.compile(r"(?ix)\bDROP\s+TABLE\b"),
        BlockReason("DROP TABLE", "dropping a table is destructive database schema deletion"),
    ),
    (
        re.compile(r"(?ix)\bgit\s+push\b(?:(?![;&|]).)*\s--force(?:-with-lease)?\b"),
        BlockReason("git push --force", "force-pushing can rewrite shared branch history"),
    ),
    (
        re.compile(r"(?ix)\bTRUNCATE\b"),
        BlockReason("TRUNCATE", "truncating removes table contents without row-by-row safeguards"),
    ),
    (
        re.compile(r"(?is)\bDELETE\s+FROM\b(?:(?!\bWHERE\b|;).)*(?:;|$)"),
        BlockReason("DELETE FROM without WHERE", "unqualified DELETE statements can remove every row"),
    ),
)


def _read_json_from_stdin() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"tool_input": {"command": raw}}
    return data if isinstance(data, dict) else {}


def _extract_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    tool_input = payload.get("tool_input") or payload.get("input") or payload.get("parameters")
    if isinstance(tool_input, dict):
        return tool_input

    env_input = os.environ.get("CLAUDE_TOOL_INPUT")
    if env_input:
        try:
            parsed = json.loads(env_input)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"command": env_input}

    return {}


def _extract_tool_name(payload: dict[str, Any]) -> str:
    return str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "")


def _extract_command(tool_input: dict[str, Any]) -> str:
    command = tool_input.get("command") or tool_input.get("cmd") or tool_input.get("script")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _normalise_for_matching(command: str) -> str:
    """Return a matching-friendly version without changing command meaning.

    shlex lets us catch quoted SQL fragments such as psql -c "DROP TABLE x" while
    preserving a raw fallback for shell metacharacters and malformed commands.
    """
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return command
    return f"{command}\n{' '.join(tokens)}"


def find_block_reason(command: str) -> BlockReason | None:
    haystack = _normalise_for_matching(command)
    for pattern, reason in BLOCK_RULES:
        if pattern.search(haystack):
            return reason
    return None


def log_blocked_attempt(command: str, project_path: str, reason: BlockReason) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason.name,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    payload = _read_json_from_stdin()
    tool_name = _extract_tool_name(payload)
    tool_input = _extract_tool_input(payload)
    command = _extract_command(tool_input)

    # Only inspect Bash tool invocations. Non-Bash tools and malformed payloads
    # should pass silently so the hook does not interfere with normal Claude use.
    if tool_name and "bash" not in tool_name.lower():
        return 0
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    log_blocked_attempt(command, project_path, reason)

    print(
        "Blocked destructive Bash command before execution.\n"
        f"Pattern: {reason.name}\n"
        f"Why: {reason.explanation}.\n"
        f"Project: {project_path}\n"
        f"Log: {LOG_PATH}\n"
        "If this action is truly required, ask the user for an explicit, scoped confirmation and use a safer command."
    )
    # Claude Code treats exit code 2 from hooks as a blocking decision.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
