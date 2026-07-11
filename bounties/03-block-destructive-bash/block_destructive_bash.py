#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Reads a JSON payload from stdin (Claude Code hooks protocol). On Bash tool
use, inspects the command string and denies known-destructive patterns.

Exit codes (Claude Code convention):
  0 — allow
  2 — block (stderr is shown to the model)

Env:
  CLAUDE_PROJECT_DIR — optional project path (set by Claude Code)
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# Patterns that always block (case-insensitive for SQL).
ALWAYS_BLOCK = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)\b"), "rm -rf (recursive force delete)"),
    (re.compile(r"\brm\s+--recursive\b.*\b--force\b|\brm\s+--force\b.*\b--recursive\b"), "rm --recursive --force"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE"),
    (re.compile(r"\bTRUNCATE\b", re.I), "TRUNCATE"),
    (re.compile(r"\bgit\s+push\b[^\n]*\s--force\b|\bgit\s+push\b[^\n]*\s-f\b"), "git push --force"),
]

# DELETE FROM without a WHERE clause (allow if WHERE present).
DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.I)
HAS_WHERE = re.compile(r"\bWHERE\b", re.I)


def extract_command(payload: dict) -> str:
    """Pull the bash command from common Claude Code hook payload shapes."""
    tool_name = (
        payload.get("tool_name")
        or payload.get("toolName")
        or payload.get("tool", {}).get("name")
        or ""
    )
    if str(tool_name).lower() not in ("", "bash", "shell"):
        # Non-bash tools: allow.
        return ""

    inp = payload.get("tool_input") or payload.get("toolInput") or payload.get("input") or {}
    if isinstance(inp, str):
        return inp
    if isinstance(inp, dict):
        for key in ("command", "cmd", "bash", "script"):
            if key in inp and isinstance(inp[key], str):
                return inp[key]
    # Some versions put command at top level.
    for key in ("command", "cmd"):
        if isinstance(payload.get(key), str):
            return payload[key]
    return ""


def find_block_reason(command: str) -> str | None:
    if not command or not command.strip():
        return None
    for pattern, reason in ALWAYS_BLOCK:
        if pattern.search(command):
            return reason
    if DELETE_FROM.search(command) and not HAS_WHERE.search(command):
        return "DELETE FROM without a WHERE clause"
    return None


def log_block(command: str, reason: str, project: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Single-line log: timestamp | project | reason | command
    line = f"{ts}\t{project}\t{reason}\t{command.replace(chr(10), ' ').replace(chr(13), ' ')}\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Unknown input: fail open so we do not brick the session.
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    project = (
        os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("PWD")
        or payload.get("cwd")
        or os.getcwd()
    )
    log_block(command, reason, str(project))

    msg = (
        f"BLOCKED by pre-tool-use safety hook: {reason}.\n"
        f"Command: {command}\n"
        f"Logged to: {LOG_PATH}\n"
        "If this was intentional, run it outside Claude Code or adjust the hook allowlist."
    )
    print(msg, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
