#!/usr/bin/env python3
"""
Claude Code PreToolUse hook: block destructive bash commands.

Reads the PreToolUse hook JSON payload from stdin (Claude Code passes the
tool name and its input there). If the tool is a Bash command that matches a
known-destructive pattern, the hook blocks it, logs the attempt, and returns
a clear explanation to Claude. All other commands pass through untouched.

Blocked patterns:
  - rm -rf                 (recursive force delete)
  - git push --force       (and --force-with-lease is allowed)
  - DROP TABLE             (SQL)
  - TRUNCATE               (SQL)
  - DELETE FROM ... without a WHERE clause (SQL)

Exit codes (per Claude Code hooks spec):
  0  -> allow (stdout is shown to the user, not to the model)
  2  -> block; stderr is fed back to the model as the block reason
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


# Each rule: (human-readable name, compiled regex, why message).
def _rules():
    return [
        (
            "rm -rf",
            # Match `rm` only when it is in COMMAND position: at the start of
            # the line or right after a shell separator (; | & && || `( ). This
            # avoids false positives like `echo "rm -rf ..."`. Requires both a
            # recursive (-r/-R/--recursive) and force (-f/--force) flag.
            re.compile(
                r"(?:^|[;&|(]|\|\||&&)\s*(?:sudo\s+)?rm\b[^\n;|&]*"
                r"(?:-\w*r\w*f|-\w*f\w*r"
                r"|-r\w*\s+[^\n;|&]*-f|-f\w*\s+[^\n;|&]*-r"
                r"|--recursive[^\n;|&]*(?:-f|--force)"
                r"|--force[^\n;|&]*(?:-r|--recursive))",
                re.IGNORECASE,
            ),
            "`rm -rf` recursively force-deletes files and is irreversible.",
        ),
        (
            "git push --force",
            # block --force / -f, but NOT --force-with-lease
            re.compile(r"\bgit\s+push\b[^\n]*(--force(?!-with-lease)\b|\s-f\b)",
                       re.IGNORECASE),
            "`git push --force` can overwrite remote history. Use "
            "`--force-with-lease` if you must force-push.",
        ),
        (
            "DROP TABLE",
            re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
            "`DROP TABLE` permanently deletes a database table.",
        ),
        (
            "TRUNCATE",
            re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
            "`TRUNCATE` removes all rows from a table and cannot be rolled "
            "back easily.",
        ),
        (
            "DELETE FROM without WHERE",
            # DELETE FROM <table> ... with no WHERE before the statement end
            re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b)[^;])*(?:;|$)",
                       re.IGNORECASE),
            "`DELETE FROM` without a `WHERE` clause deletes every row in the "
            "table.",
        ),
    ]


RULES = _rules()


def extract_command(payload: dict) -> str:
    """Pull the bash command string out of the PreToolUse payload.

    Claude Code sends the tool input under `tool_input` (older builds used
    `toolInput`). The Bash tool stores the command under `command`.
    """
    tool_input = (
        payload.get("tool_input")
        or payload.get("toolInput")
        or payload.get("input")
        or {}
    )
    if isinstance(tool_input, dict):
        cmd = tool_input.get("command", "")
        return cmd if isinstance(cmd, str) else ""
    return ""


def tool_name(payload: dict) -> str:
    return str(payload.get("tool_name") or payload.get("toolName") or "")


def match_rule(command: str):
    """Return (name, why) for the first matching destructive rule, else None."""
    for name, pattern, why in RULES:
        if pattern.search(command):
            return name, why
    return None


def log_blocked(command: str, rule_name: str) -> None:
    """Append a blocked attempt to the log (best-effort, never raises)."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        line = f"{stamp}\t{rule_name}\t{project}\t{command}\n"
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        # Logging must never break the hook itself.
        pass


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0  # nothing to inspect -> allow

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # If we can't parse, don't block legitimate work.
        return 0

    # Only inspect Bash tool calls.
    if tool_name(payload).lower() not in ("bash", ""):
        return 0

    command = extract_command(payload)
    if not command.strip():
        return 0

    hit = match_rule(command)
    if hit is None:
        return 0  # safe -> allow

    rule_name, why = hit
    log_blocked(command, rule_name)

    # Exit code 2 blocks the tool call; stderr is returned to Claude.
    sys.stderr.write(
        "BLOCKED by block-destructive-commands hook.\n"
        f"Reason: {why}\n"
        f"Matched rule: {rule_name}\n"
        "If this is intentional, run it manually outside Claude Code, or "
        "narrow the command (e.g. add a WHERE clause, use "
        "--force-with-lease, or target a specific path).\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
