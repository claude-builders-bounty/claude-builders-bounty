#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Blocks destructive shell commands and logs violations.

Enforces safe command execution across:
1. rm -rf
2. DROP TABLE / DROP DATABASE
3. git push --force / git push -f
4. TRUNCATE / TRUNCATE TABLE
5. DELETE FROM without a WHERE clause
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DANGEROUS_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b|\brm\s+--recursive\s+--force\b|\brm\s+--force\s+--recursive\b", "Recursive forced deletion (rm -rf)"),
    (r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA|VIEW)\b", "Destructive SQL DROP operation"),
    (r"\bgit\s+push\s+.*(?:--force|-f)\b", "Destructive git push force overwrite"),
    (r"\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_.]+", "Table truncation (TRUNCATE)"),
    (r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.]+(?!\s+WHERE\b)", "Unbounded SQL DELETE without WHERE clause"),
]

def check_command(command: str, project_path: str | None = None, log_file: Path | None = None) -> tuple[bool, str | None]:
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            if "DELETE" in reason and re.search(r"\bWHERE\b", command, re.IGNORECASE):
                continue
            _log_blocked_attempt(command, reason, project_path, log_file)
            return False, reason
    return True, None

def _log_blocked_attempt(command: str, reason: str, project_path: str | None = None, log_file: Path | None = None) -> None:
    target_log = log_file or Path.home() / ".claude" / "hooks" / "blocked.log"
    try:
        target_log.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "blocked_command": command,
            "violation": reason,
            "project_path": project_path or os.getcwd(),
        }
        with target_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as exc:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {exc}\n")

def main() -> int:
    command = ""
    project_path = os.getcwd()
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                try:
                    payload = json.loads(raw)
                    command = payload.get("tool_input", {}).get("command", "") or payload.get("command", "")
                    project_path = payload.get("project_path", project_path)
                except json.JSONDecodeError:
                    command = raw.strip()
        except Exception:
            pass

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if not command:
        return 0

    allowed, reason = check_command(command, project_path)
    if not allowed:
        sys.stderr.write(f"BLOCKED BY PRE-TOOL-USE HOOK: {reason}\n")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
