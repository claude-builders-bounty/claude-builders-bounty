#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive Bash commands.

Accepts JSON on stdin (Claude Code hook protocol). On match:
  - logs to ~/.claude/hooks/blocked.log
  - denies the tool call with a clear systemMessage for Claude
  - exit code 2 (blocking)

Install (2 commands) — see README.md.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Tuple

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Named patterns matching bounty acceptance criteria exactly.
# Order matters only for logging which rule fired first.
RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "rm -rf",
        re.compile(
            r"(?:^|[;&|`]|\b)\s*rm\s+(?:[^\n;|&]*\s)?-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    ),
    (
        "git push --force",
        re.compile(
            r"\bgit\s+push\b[^\n;|&]*?(?:--force(?:-with-lease)?\b|\s-f\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE),
    ),
    (
        "DELETE FROM without WHERE",
        # DELETE FROM <table> that is not followed by WHERE before end/semicolon
        re.compile(
            r"\bDELETE\s+FROM\s+[^\s;]+(?:\s+(?!WHERE\b)[^\s;]+)*\s*(?:;|$)",
            re.IGNORECASE,
        ),
    ),
]


def extract_command(payload: dict[str, Any]) -> str:
    """Pull bash command from several known payload shapes."""
    # Current Claude Code PreToolUse shape
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict) and tool_input.get("command"):
        return str(tool_input["command"])

    # Nested tool_use (some older examples)
    tool_use = payload.get("tool_use") or {}
    if isinstance(tool_use, dict):
        ti = tool_use.get("input") or {}
        if isinstance(ti, dict) and ti.get("command"):
            return str(ti["command"])

    if payload.get("command"):
        return str(payload["command"])
    return ""


def project_path(payload: dict[str, Any]) -> str:
    return (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def match_rule(command: str) -> Optional[str]:
    for name, pattern in RULES:
        if pattern.search(command):
            # Extra guard: DELETE with WHERE should not match
            if name == "DELETE FROM without WHERE":
                # If every DELETE FROM has a WHERE, allow
                for m in re.finditer(r"\bDELETE\s+FROM\b", command, re.I):
                    tail = command[m.start() :]
                    # slice until next semicolon or end
                    stmt = re.split(r"[;]", tail, maxsplit=1)[0]
                    if not re.search(r"\bWHERE\b", stmt, re.I):
                        return name
                return None
            return name
    return None


def log_block(command: str, project: str, rule: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts} | project={project} | rule={rule} | command={command}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def deny(reason: str) -> None:
    out = {
        "hookSpecificOutput": {
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
        "systemMessage": reason,
    }
    print(json.dumps(out))
    # Exit 2 also feeds stderr/message back to Claude as a blocking error.
    print(reason, file=sys.stderr)
    sys.exit(2)


def allow() -> None:
    print(json.dumps({"continue": True}))
    sys.exit(0)


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        allow()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        allow()

    tool_name = payload.get("tool_name") or payload.get("tool") or ""
    # Only enforce on Bash; never interfere with Read/Write/etc.
    if tool_name and tool_name not in ("Bash", "bash", "Shell", "shell"):
        allow()

    command = extract_command(payload)
    if not command.strip():
        allow()

    rule = match_rule(command)
    if not rule:
        allow()

    project = project_path(payload)
    log_block(command, project, rule)

    reason = (
        f"BLOCKED by pre-tool-use destructive-command hook.\n"
        f"Rule: {rule}\n"
        f"Command: {command}\n"
        f"Project: {project}\n"
        f"Logged to: {LOG_FILE}\n"
        f"Use a safer alternative (e.g. rm without -rf, DELETE ... WHERE, git push without --force)."
    )
    deny(reason)


if __name__ == "__main__":
    main()
