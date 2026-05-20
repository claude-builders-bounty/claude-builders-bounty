#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands.

The hook reads the Claude Code hook JSON payload from stdin. If the payload is for
Bash/tool command execution and the command matches a destructive pattern, it logs
the attempt and exits non-zero with a clear message. Normal commands pass through.
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


def _load_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # If Claude ever passes raw text instead of JSON, treat it as a command.
        return {"tool_input": {"command": raw}}
    return payload if isinstance(payload, dict) else {}


def _find_command(value: Any) -> str:
    """Recursively find the first command-like string in a hook payload."""
    if isinstance(value, dict):
        for key in ("command", "cmd", "bash", "script"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return candidate
        for candidate in value.values():
            found = _find_command(candidate)
            if found:
                return found
    elif isinstance(value, list):
        for candidate in value:
            found = _find_command(candidate)
            if found:
                return found
    return ""


def _blocked_reason(command: str) -> str | None:
    checks: list[tuple[str, str]] = [
        (r"\brm\s+(?:-[^\s]*r[^\s]*f|-f[^\s]*r)[\s=~/]", "recursive force removal: rm -rf"),
        (r"\bDROP\s+TABLE\b", "SQL destructive schema command: DROP TABLE"),
        (r"\bgit\s+push\b[^\n]*\s--force(?:\b|=)", "forced Git push: git push --force"),
        (r"\bTRUNCATE\b", "SQL destructive data command: TRUNCATE"),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return reason

    delete_match = re.search(r"\bDELETE\s+FROM\b", command, flags=re.IGNORECASE)
    if delete_match:
        after_delete = command[delete_match.end() :]
        # Only allow DELETE FROM when a WHERE clause appears before statement end.
        statement_tail = re.split(r";|\n", after_delete, maxsplit=1)[0]
        if not re.search(r"\bWHERE\b", statement_tail, flags=re.IGNORECASE):
            return "SQL destructive data command: DELETE FROM without WHERE"

    return None


def _log_block(command: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = _load_payload()
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    command = _find_command(payload)

    # Non-Bash tools and payloads without a command are allowed.
    if tool_name and tool_name.lower() not in {"bash", "terminal", "shell"}:
        return 0
    if not command:
        return 0

    reason = _blocked_reason(command)
    if reason is None:
        return 0

    _log_block(command, reason)
    print(
        "Blocked by Claude Code safety hook: "
        f"{reason}. The attempted command was logged to {BLOCKED_LOG}. "
        "Use a safer, narrower command or add explicit review before continuing.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
