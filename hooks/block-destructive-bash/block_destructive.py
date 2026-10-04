#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _load_input() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def _command_segments(command: str) -> list[str]:
    """Split on common shell separators for per-segment checks."""
    parts = re.split(r"(?:\s&&\s|\s\|\|\s|\s;\s|\s\|\s)", command)
    return [p.strip() for p in parts if p.strip()]


def _rm_rf(segment: str) -> bool:
    if not re.search(r"\brm\b", segment, re.I):
        return False
    if re.search(r"\brm\b[^\n|;&]*-(?:rf|fr)\b", segment, re.I):
        return True
    # rm with separate -r and -f flags (e.g. rm -r -f, rm -Rf dir)
    if re.search(r"\brm\b(?:\s+[-\w]+)+\s+", segment, re.I):
        flags = re.findall(r"-(\w+)", segment)
        flat = "".join(flags).lower()
        if "r" in flat and "f" in flat:
            return True
    return False


def _drop_table(segment: str) -> bool:
    return bool(re.search(r"\bDROP\s+TABLE\b", segment, re.I))


def _git_push_force(segment: str) -> bool:
    if not re.search(r"\bgit\s+push\b", segment, re.I):
        return False
    return bool(
        re.search(r"\bgit\s+push\b[^\n|;&]*(?:--force|--force-with-lease|\s-f\b)", segment, re.I)
    )


def _truncate(segment: str) -> bool:
    return bool(re.search(r"\bTRUNCATE\b", segment, re.I))


def _delete_from_without_where(segment: str) -> bool:
    m = re.search(r"\bDELETE\s+FROM\b", segment, re.I)
    if not m:
        return False
    rest = segment[m.start() :]
    # Statement ends at semicolon or end of segment
    end = rest.find(";")
    stmt = rest if end == -1 else rest[: end + 1]
    return not re.search(r"\bWHERE\b", stmt, re.I)


RULES: list[tuple[str, callable]] = [
    ("rm -rf (recursive force delete)", _rm_rf),
    ("DROP TABLE", _drop_table),
    ("git push --force", _git_push_force),
    ("TRUNCATE", _truncate),
    ("DELETE FROM without WHERE clause", _delete_from_without_where),
]


def check_command(command: str) -> str | None:
    for segment in _command_segments(command):
        for reason, fn in RULES:
            if fn(segment):
                return reason
    return None


def log_block(project_path: str, command: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts}\tproject={project_path}\tcommand={command}\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    data = _load_input()
    tool_name = data.get("tool_name", "")
    if tool_name and tool_name != "Bash":
        return 0

    command = (data.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        return 0

    reason = check_command(command)
    if reason is None:
        return 0

    project_path = (
        data.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    log_block(str(project_path), command)

    message = (
        f"Blocked destructive command ({reason}). "
        f"This hook prevents accidental data loss. Command was: {command!r}"
    )
    print(message, file=sys.stderr)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
