#!/usr/bin/env python3
"""
pre-tool-use.py — Claude Code pre-tool-use hook
Blocks destructive bash commands before execution.

Install: cp hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
"""

import json
import sys
import re
import os
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_DIR = os.path.dirname(LOG_FILE)

# ── Blocked patterns ─────────────────────────────────────────────────────────
BLOCKED_PATTERNS = [
    # Filesystem destruction
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b", "rm -rf: recursive force delete"),
    (r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", "rm -rf: recursive force delete"),
    # SQL destruction
    (r"\bDROP\s+TABLE\b", "DROP TABLE: irreversible schema destruction"),
    (r"\bTRUNCATE\b", "TRUNCATE: wipes entire table"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without WHERE: deletes all rows"),
    # Git force push
    (r"\bgit\s+push\b.*--force\b", "git push --force: rewrites remote history"),
    (r"\bgit\s+push\b.*-f\b", "git push -f: rewrites remote history"),
    # Extra dangerous patterns
    (r"\bdd\s+if=.*\bof=/dev/", "dd to block device: overwrites disk"),
    (r">\s*/dev/(s?d[a-z]|nvme)", "redirect to block device"),
    (r"\bchmod\s+-R\s+777\b", "chmod -R 777: world-writable permissions"),
    (r"\bmkfs\b", "mkfs: formats/destroys filesystem"),
]

def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Append a blocked attempt to the log file."""
    os.makedirs(HOOK_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | reason={reason!r} | project={project_path!r} | cmd={command!r}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def check_command(command: str) -> tuple[bool, str]:
    """Return (should_block, reason). Case-insensitive match."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not valid JSON — pass through
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = hook_input.get("cwd", os.getcwd())

    should_block, reason = check_command(command)

    if should_block:
        log_blocked(command, reason, project_path)
        output = {
            "decision": "block",
            "reason": (
                f"🛑 Blocked: {reason}\n\n"
                f"Command: {command!r}\n\n"
                "This command matches a destructive pattern and was prevented from running. "
                "If this was intentional, run it directly in your terminal. "
                f"Attempt logged to {LOG_FILE}"
            )
        }
        print(json.dumps(output))
        sys.exit(0)

    # Allow everything else
    sys.exit(0)

if __name__ == "__main__":
    main()
