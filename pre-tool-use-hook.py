#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks dangerous bash commands before execution.
Place at: ~/.claude/hooks/pre_tool_use
"""

import json
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Regex patterns for dangerous commands
DANGEROUS_PATTERNS = [
    (r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b", "rm -rf (recursive force delete)"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE (database table destruction)"),
    (r"\bgit\s+push\s+.*--force", "git push --force (force push to remote)"),
    (r"\bgit\s+push\s+.*-f\b", "git push -f (force push alias)"),
    (r"\bTRUNCATE\s+", "TRUNCATE (table data deletion)"),
    (r"\bDELETE\s+FROM\s+(?!.*\bWHERE\b)", "DELETE FROM without WHERE (full table wipe)"),
]


def log_block(command: str, reason: str, project_path: str) -> None:
    """Log blocked attempt to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = (
        f"[{datetime.now().isoformat()}] "
        f"reason={reason} "
        f"project={project_path} "
        f"command={json.dumps(command)}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches any dangerous pattern."""
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    return False, ""


def main():
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    # Only intercept Bash tool
    if tool_name != "Bash":
        output = json.dumps({"continue": True})
        sys.stdout.write(output)
        return

    if not command:
        output = json.dumps({"continue": True})
        sys.stdout.write(output)
        return

    is_dangerous, reason = check_command(command)

    if is_dangerous:
        project_path = os.getcwd()
        log_block(command, reason, project_path)

        message = (
            f"🚫 BLOCKED — {reason}\n\n"
            f"The following command was intercepted:\n"
            f"  {command}\n\n"
            f"This command is dangerous and has been blocked by the safety hook.\n"
            f"Logged to: {LOG_FILE}"
        )

        output = json.dumps({"continue": False, "reason": message})
        sys.stdout.write(output)
        return

    # Safe command — allow
    output = json.dumps({"continue": True})
    sys.stdout.write(output)


if __name__ == "__main__":
    main()
