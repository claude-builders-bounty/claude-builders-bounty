#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Interceptor
Intercepts dangerous bash commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE)
before execution, logging blocked attempts to ~/.claude/hooks/blocked.log.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b", "Recursive forced deletion (rm -rf)"),
    (r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", "Recursive forced deletion (rm -fr)"),
    (r"\bgit\s+push\b.*\b(--force|-f)\b", "Force-pushing git history (git push --force)"),
    (r"\bDROP\s+TABLE\b", "Database table deletion (DROP TABLE)"),
    (r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_.]+", "Database table truncation (TRUNCATE)"),
    (r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.]+\s*(?!.*\bWHERE\b)", "Unbounded table deletion (DELETE FROM without WHERE)"),
    (r"\b(mkfs|dd\s+if=.*of=/dev/)\b", "Disk formatting / raw write (mkfs / dd)"),
]


def log_blocked_command(cmd: str, project_dir: str, reason: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": cmd,
        "project_path": project_dir,
        "reason": reason,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        sys.exit(0)

    try:
        payload = json.loads(raw_input)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool", "") or payload.get("tool_name", "")
    if tool_name not in ("bash", "run_command", "Bash"):
        sys.exit(0)

    cmd = (payload.get("tool_input", {}) or {}).get("command", "") or payload.get("command", "")
    project_dir = payload.get("cwd", os.getcwd())

    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            log_blocked_command(cmd, project_dir, description)
            output = {
                "decision": "block",
                "reason": (
                    f"BLOCKED BY SAFETY HOOK: {description}. "
                    f"Attempted command: `{cmd}`. "
                    f"If this action is intentional, execute manually."
                ),
            }
            print(json.dumps(output))
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
