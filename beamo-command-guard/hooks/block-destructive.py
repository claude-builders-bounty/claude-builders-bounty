#!/usr/bin/env python3
"""
Claude Code PreToolUse hook — block destructive bash / SQL commands.

Install path: ~/.claude/hooks/block-destructive.py
Log path:     ~/.claude/hooks/blocked.log

Relates to: claude-builders-bounty#3
Author: Beamo LLC <beamo@beamosupport.com>
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOK_DIR / "blocked.log"

# ---------------------------------------------------------------------------
# Pattern detectors — each returns a human reason string or None
# ---------------------------------------------------------------------------

# rm with recursive (-r/--recursive) AND force (-f/--force), any flag order.
# Matches: rm -rf, rm -fr, rm -r -f, rm --force --recursive, rm -Rf, etc.
# Does NOT match: rm file, rm -f file, rm -r dir (without force)
_RE_RM_RF = re.compile(
    r"(?:^|[;&|()\s]|\$\(|`)\s*rm\s+"
    r"(?=[^|&;]*?(?:-[a-zA-Z]*[rR][a-zA-Z]*|--recursive))"
    r"(?=[^|&;]*?(?:-[a-zA-Z]*[fF][a-zA-Z]*|--force))"
    r"[^\n]*",
    re.IGNORECASE,
)

# git push --force / git push -f (not --force-with-lease alone unless --force also)
_RE_GIT_PUSH_FORCE = re.compile(
    r"(?:^|[;&|()\s]|\$\(|`)\s*git\s+push\b"
    r"(?=[^|&;\n]*?(?:--force(?:\s|$|=)|(?:\s|^)-[a-zA-Z]*f[a-zA-Z]*(?:\s|$)))",
    re.IGNORECASE,
)

# SQL: DROP TABLE
_RE_DROP_TABLE = re.compile(
    r"\bDROP\s+TABLE\b",
    re.IGNORECASE,
)

# SQL: TRUNCATE [TABLE]
_RE_TRUNCATE = re.compile(
    r"\bTRUNCATE\b",
    re.IGNORECASE,
)

# SQL: DELETE FROM ... without a WHERE clause before statement end
# Splits on ; and checks each statement-ish chunk.
_RE_DELETE_FROM = re.compile(
    r"\bDELETE\s+FROM\b",
    re.IGNORECASE,
)
_RE_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def _split_sqlish(command: str) -> list[str]:
    """Split on ; while keeping enough context for DELETE/DROP detection."""
    return [p.strip() for p in command.split(";") if p.strip()]


def check_delete_without_where(command: str) -> Optional[str]:
    for stmt in _split_sqlish(command):
        if not _RE_DELETE_FROM.search(stmt):
            continue
        # Also scan the full remaining text for WHERE after DELETE FROM
        # within this statement chunk.
        m = _RE_DELETE_FROM.search(stmt)
        assert m is not None
        after = stmt[m.end() :]
        if not _RE_WHERE.search(after):
            return (
                "Blocked: DELETE FROM without a WHERE clause can wipe an entire table. "
                "Add a WHERE filter, or use an explicit TRUNCATE only if intentional "
                "(TRUNCATE is also blocked by this hook)."
            )
    return None


def detect(command: str) -> Optional[str]:
    """Return a clear reason if the command should be blocked, else None."""
    if not command or not command.strip():
        return None

    if _RE_RM_RF.search(command):
        return (
            "Blocked: `rm` with both recursive (-r/--recursive) and force (-f/--force) "
            "can irreversibly delete directory trees. Prefer a narrower delete, move to "
            "trash, or confirm the exact path with the user first."
        )

    if _RE_GIT_PUSH_FORCE.search(command):
        return (
            "Blocked: `git push --force` / `git push -f` can overwrite remote history. "
            "Use a regular push, or `--force-with-lease` only after explicit human approval."
        )

    if _RE_DROP_TABLE.search(command):
        return (
            "Blocked: `DROP TABLE` permanently destroys a database table and its data. "
            "Confirm with the user and take a backup before running DDL like this."
        )

    if _RE_TRUNCATE.search(command):
        return (
            "Blocked: `TRUNCATE` empties a table without row-level WHERE filters. "
            "Confirm with the user before wiping table contents."
        )

    reason = check_delete_without_where(command)
    if reason:
        return reason

    return None


def extract_command(payload: dict) -> Tuple[str, str]:
    """Return (tool_name, command_string)."""
    tool_name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    return tool_name, str(command)


def project_path(payload: dict) -> str:
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return str(cwd)


def log_blocked(command: str, path: str, reason: str) -> None:
    try:
        HOOK_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # One line, tab-separated for easy grepping; reason on same line shortened
        line = f"{ts}\t{path}\t{command.replace(chr(9), ' ').replace(chr(10), ' ')}\t{reason.split(chr(10))[0]}\n"
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError as exc:
        # Logging must never prevent the block decision itself
        print(f"warning: could not write blocked.log: {exc}", file=sys.stderr)


def deny(reason: str) -> None:
    """Emit PreToolUse deny decision as JSON + exit 0 (structured), with stderr copy."""
    print(reason, file=sys.stderr)
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(decision))
    sys.exit(0)


def allow() -> None:
    sys.exit(0)


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        allow()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed input — do not block normal operation
        allow()

    tool_name, command = extract_command(payload)

    # Only inspect Bash (and PowerShell for parity); never interfere with other tools
    if tool_name and tool_name not in ("Bash", "PowerShell", "bash", "powershell"):
        allow()

    # If tool_name empty (some wrappers), still inspect if a command field exists
    if not command:
        allow()

    reason = detect(command)
    if reason is None:
        allow()

    log_blocked(command, project_path(payload), reason)
    deny(reason)


if __name__ == "__main__":
    main()
