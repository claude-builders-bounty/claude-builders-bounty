#!/usr/bin/env python3
"""Block destructive shell commands before they run.

Reads a Claude Code pre-tool-use payload on stdin. Exits 2 when the command
matches a blocked pattern, and exits 0 for everything else. A blocked attempt
is appended to the log named by HOOK_LOG, or ~/.claude/hooks/blocked.log.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RULES = [
    ("rm -rf", re.compile(r"\brm\b(?:\s+\S+)*\s+-r[^\s]*f|\brm\b(?:\s+\S+)*\s+-f[^\s]*r")),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.I)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n]*\s--force\b|\bgit\s+push\b[^\n]*\s-f\b")),
    ("DELETE FROM without WHERE", re.compile(r"\bdelete\s+from\s+\S+(?![\s\S]*\bwhere\b)", re.I)),
]


def command_from(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(tool_input, str):
        return tool_input
    for key in ("command", "cmd"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return str(payload.get("command") or "")


def project_path(payload: dict) -> str:
    for key in ("cwd", "project_dir", "project_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def matched(command: str) -> str | None:
    for name, pattern in RULES:
        if pattern.search(command):
            return name
    return None


def log_block(command: str, path: str, reason: str) -> None:
    dest = Path(os.environ.get("HOOK_LOG", Path.home() / ".claude/hooks/blocked.log"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp}\t{path}\t{reason}\t{command.replace(chr(9), ' ')}\n"
    with dest.open("a", encoding="utf-8") as handle:
        handle.write(line)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"command": raw}
    command = command_from(payload)
    reason = matched(command)
    if not reason:
        return 0
    path = project_path(payload)
    log_block(command, path, reason)
    print(f"Blocked: {reason}. The command was not run and was written to the hook log.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
