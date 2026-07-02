#!/usr/bin/env python3
"""
safe-shell-hook.py — Pre-tool-use hook for Claude Code
Blocks destructive bash commands before they execute.

Install:
  mkdir -p ~/.claude/hooks/
  cp safe-shell-hook.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/safe-shell-hook.py
"""

import json
import os
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that trigger a block
DANGEROUS_PATTERNS = [
    # Filesystem destruction
    (r"\brm\s+-rf\b", "Destructive recursive delete (rm -rf)"),
    (r"\brm\s+-r\s+/", "Recursive delete from root (rm -r /)"),
    (r"\brm\s+-rf\s+/", "Force recursive delete from root (rm -rf /)"),
    # Database destruction
    (r"\bDROP\s+TABLE", "Database table deletion (DROP TABLE)"),
    (r"\bTRUNCATE\b", "Database table truncation (TRUNCATE)"),
    (r"\bDELETE\s+FROM\b(?!\s+\w+\s+WHERE)", "DELETE without WHERE clause"),
    # Git force operations
    (r"\bgit\s+push\s+--force\b", "Force git push (git push --force)"),
    (r"\bgit\s+push\s+-f\b", "Force git push (git push -f)"),
    # Disk formatting
    (r"\bmkfs\b", "Filesystem creation (mkfs)"),
    (r"\bdd\s+if=.*\sof=", "Raw disk write (dd if=... of=...)"),
    (r"\bformat\s+[a-zA-Z]:", "Drive format command"),
    # Permission escalation
    (r"\bchmod\s+-R\s+777\b", "Recursive world-writable permissions"),
    (r"\bchown\s+-R\b", "Recursive ownership change"),
    # Network dangerous
    (r"\bwget\s+.*\|\s*bash\b", "Piped remote script execution"),
    (r"\bcurl\s+.*\|\s*bash\b", "Piped remote script execution"),
    (r"\bcurl\s+.*\|\s*sh\b", "Piped remote script execution"),
]

# Patterns that are ALWAYS OK (whitelist overrides)
SAFE_PATTERNS = [
    r"^\s*#",
    r"^\s*$",
    r"^\s*echo\b",
    r"^\s*cat\b",
    r"^\s*ls\b",
    r"^\s*grep\b",
    r"^\s*find\b",
    r"^\s*mkdir\b",
    r"^\s*touch\b",
    r"^\s*cp\b",
    r"^\s*mv\b",
    r"^\s*cd\b",
    r"^\s*pwd\b",
    r"^\s*head\b",
    r"^\s*tail\b",
    r"^\s*sort\b",
    r"^\s*uniq\b",
    r"^\s*wc\b",
    r"^\s*which\b",
    r"^\s*type\b",
    r"^\s*help\b",
    r"^\s*man\b",
    r"^\s*less\b",
    r"^\s*more\b",
]


def should_block(command: str) -> tuple[bool, str]:
    """Check if a command is dangerous. Returns (block, reason)."""
    cmd_stripped = command.strip()

    # Always allow safe commands
    for pattern in SAFE_PATTERNS:
        import re
        if re.search(pattern, cmd_stripped, re.IGNORECASE):
            return False, ""

    # Check dangerous patterns
    for pattern, reason in DANGEROUS_PATTERNS:
        import re
        if re.search(pattern, cmd_stripped, re.IGNORECASE):
            return True, reason

    return False, ""


def log_block(command: str, reason: str, project_path: str) -> None:
    """Log blocked command to log file."""
    timestamp = datetime.now(timezone.utc).isoformat()
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, mode=0o755, exist_ok=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] BLOCKED: {reason}\n")
            f.write(f"  Command: {command}\n")
            f.write(f"  Project: {project_path}\n\n")
    except OSError:
        pass  # Silently fail if we can't write the log


def main():
    try:
        # Read the JSON input from Claude
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, KeyError) as e:
        # If we can't parse input, allow the command silently
        print(json.dumps({"result": {"status": "allowed"}}))
        sys.exit(0)

    # Extract tool info
    tool_use = input_data.get("toolUse", {})
    tool_name = tool_use.get("name", "")
    tool_input = tool_use.get("input", {})

    # Only intercept bash commands
    if tool_name not in ("Bash", "bash", "execute_command", "command"):
        print(json.dumps({"result": {"status": "allowed"}}))
        sys.exit(0)

    command = tool_input.get("command", "") or tool_input.get("cmd", "")

    project_path = os.getcwd()

    block, reason = should_block(command)

    if block:
        log_block(command, reason, project_path)

        message = (
            f"⚠️ **BLOCKED**: {reason}\n\n"
            f"This command was blocked by the safe-shell-hook for your protection.\n"
            f"Blocked: `{command}`\n\n"
            f"*If you need to run this command intentionally, use an alternative approach:*\n"
            f"- For deletes: use trash/bin instead\n"
            f"- For DB changes: use safe migrations\n"
            f"- For git force: use `git push --force-with-lease`\n\n"
            f"*Block logged to: ~/.claude/hooks/blocked.log*"
        )

        print(json.dumps({
            "result": {
                "status": "blocked",
                "message": message,
                "reason": reason,
                "command": command
            }
        }))
    else:
        # Allow the command
        print(json.dumps({"result": {"status": "allowed"}}))


if __name__ == "__main__":
    main()
