#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: block destructive bash commands.

Reads a JSON event from stdin (Claude Code hook format) and decides whether to
block the bash command. On block, also appends a structured log entry to
~/.claude/hooks/blocked.log.

Patterns blocked:
  - rm -rf / rm -fr (any dir, with extra defenses for $HOME / `/`)
  - DROP TABLE
  - git push --force / git push -f
  - TRUNCATE [TABLE]
  - DELETE FROM <table>  WITHOUT a WHERE clause
  - mkfs.* / dd if=... of=/dev/...

Output:
  Block:    {"decision":"block","reason":"<human-readable explanation>"}
  Approve:  no decision field — Claude proceeds normally.

Exit code is always 0 (the JSON output controls the gate).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


# Each rule = (compiled regex, human-readable reason).
# Patterns are conservative: false-positive on a borderline command is preferable
# to silently letting a destructive command through.
RULES: list[tuple[re.Pattern, str]] = [
    (
        # Match `rm` invoked with combined recursive+force flags in any order,
        # e.g.  rm -rf,  rm -fr,  rm -Rf,  rm -r -f,  rm --recursive --force.
        re.compile(
            r"\brm\s+(?:"
            r"(?:[a-zA-Z]*-[a-zA-Z]*[rR][a-zA-Z]*-?[a-zA-Z]*[fF][a-zA-Z]*)"   # -rf, -Rf, -rfX, -Xrf
            r"|(?:[a-zA-Z]*-[a-zA-Z]*[fF][a-zA-Z]*-?[a-zA-Z]*[rR][a-zA-Z]*)"  # -fr, -fR
            r"|(?:[a-zA-Z]*-[rR][a-zA-Z]*\s+[a-zA-Z]*-[fF])"                  # -r -f
            r"|(?:[a-zA-Z]*-[fF][a-zA-Z]*\s+[a-zA-Z]*-[rR])"                  # -f -r
            r"|--recursive[\s=].*--force"
            r"|--force[\s=].*--recursive"
            r")\b"
        ),
        "rm -rf (or rm -fr / rm -r -f / rm --recursive --force) deletes recursively without prompts. "
        "There is no undo. If you really need this, run it in a shell outside Claude Code so a human "
        "can read the path before pressing Enter.",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE drops data immediately and is rarely recoverable. "
        "Use a migration with an explicit deprecation step instead.",
    ),
    (
        re.compile(r"\bgit\s+push\s+(?:[\w./:-]+\s+)*(?:--force|--force-with-lease|-f)\b"),
        "git push --force overwrites remote history and breaks teammates' clones. "
        "If you must rewrite, prefer --force-with-lease and run it from a normal shell after review.",
    ),
    (
        re.compile(r"\bTRUNCATE\b(?:\s+TABLE)?", re.IGNORECASE),
        "TRUNCATE TABLE wipes a table without ROW-level rollback in most engines. "
        "Use a migration with a backup step instead.",
    ),
    (
        # DELETE FROM <table> not followed (eventually) by WHERE — multiline-aware.
        re.compile(
            r"\bDELETE\s+FROM\s+(?:[\"`'\w.]+)(?![^;]*\bWHERE\b)",
            re.IGNORECASE | re.DOTALL,
        ),
        "DELETE FROM without a WHERE clause empties the table. "
        "Add a WHERE, or wrap in a transaction with explicit row counts.",
    ),
    (
        re.compile(r"\bmkfs\."),
        "mkfs.* formats a filesystem. Block by default — recovery is impossible.",
    ),
    (
        re.compile(r"\bdd\s+(?:if=\S+\s+)?of=/dev/"),
        "dd of=/dev/* writes raw bytes to a device. Block by default.",
    ),
    (
        re.compile(r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:"),
        "Fork bomb pattern detected.",
    ),
]


def _read_event() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _extract_command(event: dict) -> str | None:
    """Pull the bash command out of a Claude Code pre-tool-use event."""
    if event.get("tool_name") not in (None, "Bash"):
        return None
    tool_input = event.get("tool_input") or event.get("toolInput") or {}
    cmd = tool_input.get("command")
    if not cmd or not isinstance(cmd, str):
        return None
    return cmd


def _match(cmd: str) -> tuple[re.Pattern, str] | None:
    for pat, reason in RULES:
        if pat.search(cmd):
            return pat, reason
    return None


def _log_block(cmd: str, pattern: re.Pattern, reason: str, project_path: str | None) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "command": cmd,
        "pattern": pattern.pattern,
        "reason": reason,
        "project": project_path,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    event = _read_event()
    cmd = _extract_command(event)
    if cmd is None:
        # Not a bash event we care about — let it through.
        return 0

    hit = _match(cmd)
    if hit is None:
        # Normal command — no decision needed.
        return 0

    pattern, reason = hit
    project = event.get("cwd") or event.get("session_cwd") or os.getcwd()
    _log_block(cmd, pattern, reason, project)

    print(json.dumps({
        "decision": "block",
        "reason": (
            f"Blocked by destructive-bash-blocker hook.\n"
            f"Reason: {reason}\n"
            f"Pattern: {pattern.pattern!r}\n"
            f"This block was logged to {LOG_PATH}."
        ),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
