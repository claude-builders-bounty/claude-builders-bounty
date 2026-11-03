#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
Follows Claude Code hooks format (~/.claude/hooks/)
Solves Bounty #3 ($100) in claude-builders-bounty.
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path

# Patterns required by acceptance criteria:
# 1. rm -rf (including variants like -fr, -r -f, --force --recursive)
# 2. DROP TABLE
# 3. git push --force / -f / --force-with-lease
# 4. TRUNCATE
# 5. DELETE FROM without a WHERE clause
DANGEROUS_PATTERNS = [
    (
        r"\brm\s+.*(?:-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b|--force.*--recursive|--recursive.*--force|-r\s+-f|-f\s+-r)",
        "Recursive forced file removal (rm -rf)"
    ),
    (
        r"\bDROP\s+TABLE\b",
        "Destructive SQL schema command (DROP TABLE)"
    ),
    (
        r"\bgit\s+push\b.*(?:\s+--force\b|\s+-f\b|\s+--force-with-lease\b)",
        "Forced git push history overwrite (git push --force)"
    ),
    (
        r"\bTRUNCATE(?:\s+TABLE)?\s+[a-zA-Z0-9_`\"'\.]+\b",
        "Destructive SQL table wipe (TRUNCATE)"
    ),
    (
        r"\bDELETE\s+FROM\s+[a-zA-Z0-9_`\"'\.]+(?!\s+(?:WHERE\b|RETURNING\b.*\bWHERE\b))(?:\s*;|\s*$)",
        "Unconstrained SQL delete without WHERE clause"
    ),
]

def log_blocked(command: str, cwd: str, reason: str):
    """Logs blocked attempts to ~/.claude/hooks/blocked.log with timestamp, command, and project path."""
    try:
        log_dir = Path.home() / ".claude" / "hooks"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "blocked.log"

        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] BLOCKED: \"{command}\" | CWD: {cwd} | REASON: {reason}\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write to blocked.log: {e}\n")

def check_command(command: str) -> tuple[bool, str]:
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    return False, ""

def main():
    # Read Claude Code pre-tool-use payload from stdin
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)

        # Parse JSON payload if sent by Claude Code
        if raw_input.strip().startswith("{"):
            payload = json.loads(raw_input)
            tool_name = payload.get("tool_name", "")
            tool_input = payload.get("tool_input", {})
            cwd = payload.get("cwd", os.getcwd())

            # Only inspect bash / command execution tools
            if tool_name not in ["bash", "execute_command", "shell", "run_command"]:
                sys.exit(0)

            command = tool_input.get("command", "") or tool_input.get("cmd", "") or tool_input.get("CommandLine", "")
        else:
            # Direct string input fallback
            command = raw_input.strip()
            cwd = os.getcwd()
    except Exception:
        # Fallback to allow normal execution if input cannot be parsed
        sys.exit(0)

    if not command:
        sys.exit(0)

    is_dangerous, reason = check_command(command)

    if is_dangerous:
        log_blocked(command, cwd, reason)
        error_message = (
            f"\n🚨 [BLOCKED BY HOOK] Destructive bash command intercepted!\n"
            f"Command: {command}\n"
            f"Detected Hazard: {reason}\n"
            f"Explanation: For safety, irreversible commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, and DELETE without WHERE) "
            f"are blocked automatically. Please use safe non-destructive flags or targeted queries with explicit WHERE clauses.\n"
        )
        sys.stderr.write(error_message)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
