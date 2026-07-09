#!/usr/bin/env python3
"""Claude Code PreToolUse hook — block destructive bash commands.

Intercepts `Bash` tool calls before execution. If the command matches a known
destructive pattern it is BLOCKED (exit code 2, reason shown to Claude) and the
attempt is appended to ~/.claude/hooks/blocked.log. Anything else is allowed
(exit 0), so normal commands are untouched.

Blocked patterns:
  - `rm -rf`            recursive + force file deletion (any flag order / long forms)
  - `git push --force`  force push (also `-f`)
  - `DROP TABLE`        destructive schema change
  - `TRUNCATE`          table truncation
  - `DELETE FROM` without a `WHERE` clause   unbounded row deletion

Install: copy to ~/.claude/hooks/ and register as a PreToolUse hook (see README).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _hooks_dir() -> Path:
    override = os.environ.get("CLAUDE_HOOKS_DIR")
    base = Path(override) if override else Path.home() / ".claude" / "hooks"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _rm_rf(cmd: str) -> bool:
    m = re.search(r"(?:^|[\s;|&(])rm\b(.*)$", cmd, re.S)
    if not m:
        return False
    tail = m.group(1)
    has_r = bool(re.search(r"(?:^|\s)-[a-zA-Z]*r[a-zA-Z]*(?:\s|$)", tail)) or "--recursive" in tail
    has_f = bool(re.search(r"(?:^|\s)-[a-zA-Z]*f[a-zA-Z]*(?:\s|$)", tail)) or "--force" in tail
    return has_r and has_f


def _force_push(cmd: str) -> bool:
    # Block bare `--force` / `-f`, but allow the safe everyday `--force-with-lease`.
    if not re.search(r"\bgit\s+push\b", cmd):
        return False
    return bool(re.search(r"--force(?!-with-lease)\b", cmd) or re.search(r"(?:^|\s)-f\b", cmd))


def detect(command: str) -> str | None:
    """Return a human reason if the command is destructive, else None."""
    cmd = command.strip()
    if _rm_rf(cmd):
        return "recursive, forced file deletion (`rm -rf`)"
    if _force_push(cmd):
        return "force push can overwrite remote history (`git push --force`)"
    if re.search(r"\bDROP\s+TABLE\b", cmd, re.I):
        return "destructive schema change (`DROP TABLE`)"
    if re.search(r"\bTRUNCATE\b", cmd, re.I):
        return "table truncation removes all rows (`TRUNCATE`)"
    if re.search(r"\bDELETE\s+FROM\b", cmd, re.I) and not re.search(r"\bWHERE\b", cmd, re.I):
        return "unbounded row deletion (`DELETE FROM` without a `WHERE` clause)"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # not parseable as a hook event -> do not interfere
    if payload.get("tool_name") != "Bash":
        return 0
    command = str((payload.get("tool_input") or {}).get("command", ""))
    if not command.strip():
        return 0

    reason = detect(command)
    if reason is None:
        return 0  # safe -> allow

    project = payload.get("cwd") or os.getcwd()
    log_path = _hooks_dir() / "blocked.log"
    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now(timezone.utc).isoformat()}\t{project}\t{command}\n")
    except OSError:
        pass  # never let logging failure crash the hook

    sys.stderr.write(
        "BLOCKED by block-destructive-bash hook.\n"
        f"Reason: {reason}\n"
        f"Command: {command}\n"
        f"Logged to: {log_path}\n"
        "If this is truly intended, run it yourself in a terminal outside Claude Code.\n")
    return 2  # PreToolUse: non-zero (2) blocks the tool call and shows stderr to Claude


if __name__ == "__main__":
    raise SystemExit(main())
