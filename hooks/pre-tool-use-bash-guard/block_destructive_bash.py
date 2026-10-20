#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Command Guard (Bounty #3)
Intercepts dangerous Bash tool invocations before execution, logs blocked attempts
to ~/.claude/hooks/blocked.log, and returns a structured block message to Claude.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

DESTRUCTIVE_PATTERNS = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive)\b", re.IGNORECASE), "Recursive force deletion (`rm -rf`) is prohibited."),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "SQL `DROP TABLE` destructive schema operation is prohibited."),
    (re.compile(r"\bgit\s+push\s+.*(--force\b|-f\b)", re.IGNORECASE), "Force pushing (`git push --force`) is prohibited."),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "SQL `TRUNCATE` operation is prohibited."),
    (re.compile(r"\bDELETE\s+FROM\s+[A-Za-z0-9_.`\"']+\s*(?:;|$)", re.IGNORECASE), "Unbounded `DELETE FROM` without a `WHERE` clause is prohibited."),
]


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] project={project_path} | command={json.dumps(command)} | reason={reason}\n"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(entry)


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name") or payload.get("tool") or ""
    if tool_name.lower() not in ("bash", "execute_command", "run_terminal_cmd", ""):
        return 0

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else str(tool_input)
    if not command:
        return 0

    project_path = payload.get("cwd") or os.getcwd()

    for regex, reason in DESTRUCTIVE_PATTERNS:
        if regex.search(command):
            log_blocked_attempt(command, project_path, reason)
            msg = (
                f"🛑 BLOCKED BY CLAUDE PRE-TOOL-USE HOOK: {reason}\n"
                f"Attempted command: `{command}`\n"
                f"Logged to: ~/.claude/hooks/blocked.log\n"
                f"Please rewrite using a non-destructive alternative (e.g., targeted file removal, WHERE clause, or --force-with-lease Only when explicitly approved)."
            )
            print(json.dumps({"decision": "block", "reason": msg}))
            sys.stderr.write(msg + "\n")
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
