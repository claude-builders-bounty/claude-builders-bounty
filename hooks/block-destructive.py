#!/usr/bin/env python3
"""
Claude Code PreToolUse hook that blocks destructive bash commands.

Reads the PreToolUse event JSON from stdin and inspects the command for
patterns that are likely to cause data loss or unrecoverable state changes.
Blocked patterns:

  - rm -rf / rm -fr / rm -Rf / rm --recursive --force (BOTH recursive AND force)
  - DROP TABLE / DROP DATABASE / DROP SCHEMA / DROP INDEX / DROP VIEW / ...
  - git push --force (and -f / --force-with-lease)
  - TRUNCATE [TABLE] <name>
  - DELETE FROM <table> without a WHERE / USING clause

Exit codes (per Claude Code hooks contract):
  0 -> allow the tool call
  2 -> block the tool call; the message on stderr is surfaced to Claude

All blocked attempts are appended to ~/.claude/hooks/blocked.log with the
timestamp, project working directory, attempted command, and matched rule.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(
    os.environ.get(
        "DESTRUCTIVE_HOOK_LOG",
        Path.home() / ".claude" / "hooks" / "blocked.log",
    )
)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


# rm: must contain BOTH recursive (r/R) AND force (f/F) — either in the same
# short-flag cluster or as separate short flags, or as long-flag form.
# Examples blocked: rm -rf, rm -fr, rm -Rf, rm -fR, rm -frv, rm -rfv,
#                   rm --recursive --force, rm --force --recursive
# Examples allowed: rm -f, rm -r, rm -i, rm -v, rm file, rm -rf*.bak
_RM_SHORT = re.compile(
    r"\brm\b"
    r"(?:\s+-(?=[^\s]*[rR])(?=[^\s]*[fF])[a-zA-Z]+)"  # single -xyz cluster with both r/R and f/F
    r"(?:\s+-(?=[^\s]*[rR])(?=[^\s]*[fF])[a-zA-Z]+)*",  # additional clusters (e.g. -rfv -Rf)
    re.IGNORECASE,
)
_RM_LONG = re.compile(
    r"\brm\b"
    r"(?=(?:[^\n]*\s--recursive\b[^\n]*\s--force\b)"
    r"|(?:[^\n]*\s--force\b[^\n]*\s--recursive\b))",
    re.IGNORECASE,
)

# SQL DROP statements (DROP TABLE / DATABASE / SCHEMA / INDEX / VIEW / ...)
_DROP = re.compile(
    r"\bdrop\s+(table|database|schema|index|view|function|procedure|"
    r"sequence|trigger|role|user)\b",
    re.IGNORECASE,
)

# git push --force: --force, --force-with-lease, or -f
# The two flags can appear in either order with anything (including newlines
# if the command spans lines, but for shell single-line is the common case).
_GIT_FORCE_PUSH = re.compile(
    r"\bgit\b[^\n;]*\bpush\b"
    r"(?=[^\n;]*"
    r"(?:\s-f\b|\s--force\b|\s--force-with-lease\b|\s--force-if-includes\b)"
    r")",
    re.IGNORECASE,
)

# TRUNCATE [TABLE] <name>
_TRUNCATE = re.compile(
    r"\btruncate\b(?:\s+table)?\s+[`\"\[]?[\w$.]+",
    re.IGNORECASE,
)

# DELETE FROM <name> with NO WHERE / USING / RETURNING / LIMIT / FOR / etc.
# Strip SQL comments first.
_DELETE_NO_WHERE = re.compile(
    r"\bdelete\b\s+from\s+[`\"\[]?[\w$.]+"
    r"(?!\s+(?:where|using|returning|limit|order\s+by|offset|for\s+|with\s+))"
    r"\s*(?:;|$|--|/\*|\Z)",
    re.IGNORECASE,
)


def _strip_sql_comments(command: str) -> str:
    """Remove SQL line and block comments so 'WHERE /* kept */ 1=1' is
    recognised as having a WHERE clause."""
    command = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    command = re.sub(r"--[^\n]*", " ", command)
    return command


def match_rule(command: str) -> str | None:
    """Return the rule label for the first matching pattern, or None.

    SQL comment stripping is applied before evaluating the DELETE rule;
    other rules intentionally operate on the raw command so that
    `psql -c 'DROP TABLE users'` is still blocked (the SQL sits inside a
    string literal but the surrounding command is the destructive action).
    """
    if _RM_SHORT.search(command) or _RM_LONG.search(command):
        return "rm --recursive --force"
    if _DROP.search(command):
        return "DROP <object>"
    if _GIT_FORCE_PUSH.search(command):
        return "git push --force"
    if _TRUNCATE.search(command):
        return "TRUNCATE"
    if _DELETE_NO_WHERE.search(_strip_sql_comments(command)):
        return "DELETE FROM without WHERE"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse the payload, fail open — don't break Claude.
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    matched = match_rule(command)
    if matched is None:
        return 0

    project_path = payload.get("cwd") or os.getcwd()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    log_line = f"{timestamp}\t{project_path}\t{matched}\t{command}\n"
    try:
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(log_line)
    except OSError:
        # Don't let logging failures cause false positives for the user.
        pass

    reason = (
        f"BLOCKED by destructive-bash hook: matched rule {matched!r}.\n"
        f"  - If this command is intentional, run it directly in your shell "
        f"instead of asking Claude to execute it.\n"
        f"  - Audit log: {LOG_PATH}"
    )
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
