#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands.

Registered as a PreToolUse hook on the Bash tool. Reads the hook payload from
stdin, inspects the command, and either allows it (exit 0, no output) or
blocks it by emitting a JSON decision. Every blocked attempt is appended to
~/.claude/hooks/blocked.log with a timestamp, the attempted command and the
project path.

Fail-open by design: any internal error lets the command through rather than
bricking the session. The goal is to catch obvious foot-guns, not to be a
security boundary.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOK_DIR / "blocked.log"

# Each entry is (human label, compiled regex). Matching is case-insensitive
# for the SQL keywords; rm/git matching keeps the conventional casing.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.I)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.I)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^;&|\n]*--force\b", re.I)),
    ("git push -f", re.compile(r"\bgit\s+push\b[^;&|\n]*(?:^|\s)-f(?:\s|$)", re.I)),
]


def _rm_is_destructive(command: str) -> bool:
    """True if an rm invocation carries both -r and -f (in any flag spelling)."""
    for m in re.finditer(r"\brm\b([^;&|\n]*)", command, re.I):
        flags = m.group(1)
        # collect single-letter flags from -x / -xyz clusters
        letters = set()
        for cluster in re.findall(r"(?<!\w)-[a-zA-Z]+", flags):
            letters.update(cluster.lstrip("-").lower())
        if "r" in letters and "f" in letters:
            return True
    return False


def _has_delete_without_where(command: str) -> bool:
    """True if a DELETE FROM statement has no WHERE clause."""
    # Split on statement terminators so a multi-statement command is handled
    # per statement.
    for stmt in re.split(r";", command):
        m = re.search(r"\bDELETE\s+FROM\b", stmt, re.I)
        if not m:
            continue
        # Anything after DELETE FROM up to end-of-statement; if no WHERE, block.
        tail = stmt[m.end():]
        if not re.search(r"\bWHERE\b", tail, re.I):
            return True
    return False


def _is_destructive(command: str) -> str | None:
    if _rm_is_destructive(command):
        return "rm -rf"
    for label, pattern in PATTERNS:
        if pattern.search(command):
            return label
    if _has_delete_without_where(command):
        return "DELETE FROM without WHERE"
    return None


def _log(command: str, project: str, reason: str) -> None:
    try:
        HOOK_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp}\t{reason}\t{project}\t{command}\n")
    except OSError:
        # Logging must never block or crash the hook.
        pass


def main() -> int:
    try:
        raw = sys.stdin.read()
    except Exception:
        return 0
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return 0

    if not isinstance(payload, dict):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = _is_destructive(command)
    if reason is None:
        return 0

    project = payload.get("cwd") or os.getcwd()
    _log(command, str(project), reason)

    decision = {
        "decision": "block",
        "reason": (
            f"Blocked by destructive-command hook ({reason}). "
            "This command can cause irreversible data loss. "
            "If you are certain it is safe, run it manually in a terminal."
        ),
    }
    sys.stdout.write(json.dumps(decision))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
