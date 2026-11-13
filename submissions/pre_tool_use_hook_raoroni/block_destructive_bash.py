#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Blocks destructive Bash commands before execution.
Follows the official Claude Code hooks specification (~/.claude/hooks/).
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

DESTRUCTIVE_RULES = [
    (
        re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive)\b", re.I),
        "Destructive file deletion ('rm -rf') is blocked by safety policy.",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.I),
        "Destructive SQL operation ('DROP TABLE') is blocked by safety policy.",
    ),
    (
        re.compile(r"\bgit\s+push\b[^\n;|&]*(\s--force\b|\s-f\b|\s--force-with-lease\b)", re.I),
        "Force pushing ('git push --force') is blocked to prevent remote history loss.",
    ),
    (
        re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_.`\"']+", re.I),
        "Table truncation ('TRUNCATE') is blocked by safety policy.",
    ),
]

DELETE_FROM_RE = re.compile(
    r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.`\"']+(?:\s+(?!WHERE\b)[^;\n]*)?(?:;|$)",
    re.I,
)
HAS_WHERE_RE = re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.`\"']+\s+WHERE\s+\S+", re.I)


def inspect_bash_command(command: str) -> str | None:
    """Returns a clear block reason if the command matches any destructive pattern, or None if safe."""
    if not command or not command.strip():
        return None

    for pattern, reason in DESTRUCTIVE_RULES:
        if pattern.search(command):
            return reason

    if re.search(r"\bDELETE\s+FROM\b", command, re.I):
        if not HAS_WHERE_RE.search(command):
            return "Unbounded SQL deletion ('DELETE FROM' without a 'WHERE' clause) is blocked by safety policy."

    return None


def log_blocked_attempt(command: str, project_path: str, log_path: Path = LOG_FILE) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] project={project_path} | command={json.dumps(command)}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def main() -> int:
    try:
        raw_stdin = sys.stdin.read().strip()
        payload = json.loads(raw_stdin) if raw_stdin else {}
    except Exception:
        payload = {}

    tool_name = payload.get("tool_name") or payload.get("tool") or "Bash"
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, str):
        command = tool_input
    else:
        command = str(tool_input.get("command") or os.environ.get("CLAUDE_TOOL_COMMAND") or "")

    project_path = str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())

    if tool_name.lower() not in ("bash", "shell", ""):
        return 0

    reason = inspect_bash_command(command)
    if reason:
        log_blocked_attempt(command=command, project_path=project_path)
        response = {
            "decision": "block",
            "reason": f"BLOCKED BY PRE-TOOL-USE HOOK: {reason} (Command: `{command}`)",
        }
        print(json.dumps(response))
        print(response["reason"], file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

