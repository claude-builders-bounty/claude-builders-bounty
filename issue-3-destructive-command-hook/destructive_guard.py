#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    for key in ("command", "cmd"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def destructive_reason(command: str) -> str | None:
    text = " ".join(command.strip().split())
    lower = text.lower()

    if re.search(r"(^|[;&|()]|\s)rm\s+(?:-[^\s]*r[^\s]*f[^\s]*|-[^\s]*f[^\s]*r[^\s]*)\b", lower):
        return "recursive forced removal (rm -rf/rm -fr)"

    if re.search(r"\bgit\s+push\b[^\n;|&]*\s--force(?:-with-lease)?\b", lower) or re.search(
        r"\bgit\s+push\b[^\n;|&]*\s-f(?:\s|$)", lower
    ):
        return "forced git push"

    if re.search(r"\bdrop\s+table\b", lower):
        return "DROP TABLE"

    if re.search(r"\btruncate(?:\s+table)?\b", lower):
        return "TRUNCATE"

    # Inspect each SQL-ish statement independently so a WHERE in a later statement
    # cannot accidentally make an earlier unsafe DELETE appear safe.
    for statement in re.split(r"[;\n]+", text):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, flags=re.IGNORECASE
        ):
            return "DELETE FROM without WHERE"

    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    hook_dir = Path.home() / ".claude" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    log_path = hook_dir / "blocked.log"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # A malformed hook payload is not itself evidence of a dangerous command.
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = destructive_reason(command)
    if not reason:
        return 0

    project_path = str(
        payload.get("cwd")
        or payload.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    log_block(command, project_path, reason)
    print(
        f"Blocked destructive Bash command: {reason}. "
        "Use a safer, scoped alternative or ask the user for explicit confirmation.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
