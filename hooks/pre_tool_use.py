#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code.
Blocks destructive bash commands before execution.

Hook format: reads JSON from stdin, writes result to stdout/stderr.
Claude Code passes: {"tool_name": "Bash", "tool_input": {"command": "..."}, ...}
Hook exits with code 2 to block, stderr message sent back to Claude.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Patterns that require blocking. Each entry: (compiled regex, reason)
DANGEROUS_PATTERNS = [
    # Filesystem destruction
    (re.compile(r"\brm\s+(-[rfRF]+\s+)+(/.{0,3}/|~|\$)", re.IGNORECASE),
     "Recursive forced deletion of sensitive path"),
    (re.compile(r"\brm\s+-rf\s+\S+", re.IGNORECASE),
     "Recursive forced deletion (rm -rf)"),
    (re.compile(r"\bchmod\s+-R\s+777\b", re.IGNORECASE),
     "Recursive 777 chmod"),
    (re.compile(r"\bmv\s+\S+\s+/dev/null\b", re.IGNORECASE),
     "Moving files to /dev/null"),
    (re.compile(r"\bdd\s+if=\S+\s+of=/dev/(sd[a-z]|vd[a-z]|nvme)\b", re.IGNORECASE),
     "Direct disk overwrite with dd"),

    # Database destruction
    (re.compile(r"\bDROP\s+(TABLE|DATABASE)\b", re.IGNORECASE),
     "DROP TABLE/DATABASE detected"),
    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w+\s*;?\s*$", re.IGNORECASE),
     "TRUNCATE TABLE detected"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*;?\s*$", re.IGNORECASE),
     "DELETE FROM without WHERE clause"),

    # Git destruction
    (re.compile(r"\bgit\s+push\s+(--force|-f)\b", re.IGNORECASE),
     "Force push detected"),
    (re.compile(r"\bgit\s+push\s+--force\s+--thin\b", re.IGNORECASE),
     "Force push with thin pack"),
    (re.compile(r"\bgit\s+checkout\s+--\s+(\.|\*)", re.IGNORECASE),
     "Discard all local changes"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
     "Hard reset detected"),
    (re.compile(r"\bgit\s+clean\s+-fd\b", re.IGNORECASE),
     "Force clean untracked files/dirs"),
    (re.compile(r"\bgit\s+branch\s+-D\b", re.IGNORECASE),
     "Force-delete branch"),

    # Fork bombs & resource exhaustion
    (re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;:\s*$", re.IGNORECASE),
     "Fork bomb detected"),
    (re.compile(r"\bwhile\s+true\b", re.IGNORECASE),
     "Infinite while loop"),

    # Privilege escalation
    (re.compile(r"\bsudo\s+rm\s+-rf\b", re.IGNORECASE),
     "sudo rm -rf detected"),
    (re.compile(r"\bsudo\s+chmod\s+-R\b", re.IGNORECASE),
     "sudo chmod -R detected"),
    (re.compile(r"\bsudo\s+chown\s+-R\b", re.IGNORECASE),
     "sudo chown -R detected"),

    # Network attacks / data exfil
    (re.compile(r"\bcurl\s+.*\|\s*(bash|sh|zsh)\b", re.IGNORECASE),
     "Piping curl to shell"),
    (re.compile(r"\bwget\s+.*\|\s*(bash|sh|zsh)\b", re.IGNORECASE),
     "Piping wget to shell"),
    (re.compile(r"\bnc\s+(-[a-z]*\s+)*-[lv]\b", re.IGNORECASE),
     "Netcat listener/connection"),
    (re.compile(r"\bscp\s+.*@(root|admin)\b", re.IGNORECASE),
     "SCP to privileged remote user"),

    # Low-level device attacks
    (re.compile(r"\b(mkfs|mke2fs|mkreiserfs|mkfs\.ext[34])\b", re.IGNORECASE),
     "Filesystem formatting tool detected"),
    (re.compile(r"\b(>|\>\>)\s*/dev/(sd[a-z]|vd[a-z]|nvme)\b", re.IGNORECASE),
     "Writing directly to block device"),
    (re.compile(r"\btruncate\s+-s\s+0\s+/etc/(passwd|shadow)\b", re.IGNORECASE),
     "Truncating critical system file"),
]


def log_blocked(command: str, reason: str) -> None:
    """Append a blocked-attempt entry to the log file."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    project = str(Path.cwd())
    entry = f"[{timestamp}] BLOCKED: {reason}\n  command: {command}\n  project: {project}\n"
    try:
        with LOG_FILE.open("a") as f:
            f.write(entry)
    except OSError:
        pass  # Never crash the hook because of a logging failure


def is_dangerous(command: str) -> tuple[bool, str]:
    """Return (blocked, reason) for a given command string."""
    cmd = command.strip()
    if not cmd:
        return False, ""

    for compiled, reason in DANGEROUS_PATTERNS:
        if compiled.search(cmd):
            return True, reason

    return False, ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Malformed input — allow through rather than break the session
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # Only inspect Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    blocked, reason = is_dangerous(command)
    if not blocked:
        sys.exit(0)

    # Log the attempt
    log_blocked(command, reason)

    # Exit code 2 = block the tool use, stderr goes back to Claude
    message = (
        f"BLOCKED by pre_tool_use hook\n"
        f"Reason: {reason}\n"
        f"Claude, this command was intercepted because it matches a dangerous pattern.\n"
        f"Please choose a safer alternative or explain why this is necessary."
    )
    print(message, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
