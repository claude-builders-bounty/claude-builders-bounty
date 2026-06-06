#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Intercepts dangerous patterns before execution and logs blocked attempts.

Patterns blocked:
  - rm -rf (and variants)
  - DROP TABLE / DROP DATABASE
  - git push --force / git push -f
  - TRUNCATE TABLE
  - DELETE FROM without WHERE clause
  - :(){ :|:& };: (fork bomb)
  - chmod 777
  - > /dev/sda (raw device writes)
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# 鈹€鈹€ Dangerous patterns 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
DANGEROUS = [
    # rm -rf and variants (handles -rf, -fr, -r -f, --recursive, etc.)
    (r"\brm\s+.*(-[a-z]*[rR][a-z]*[fF]|-[a-z]*[fF][a-z]*[rR])[a-z]*\b", "rm with recursive+force flags"),
    (r"\brm\s+.*-[rR]\b.*-[fF]\b", "rm -r ... -f (separate flags)"),
    (r"\brm\s+.*--recursive\b", "rm --recursive"),
    # SQL destruction
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE"),
    # Force push
    (r"\bgit\s+push\s+.*(--force|-f)\b", "git push --force"),
    # Truncate
    (r"\bTRUNCATE\s+TABLE\b", "TRUNCATE TABLE"),
    # DELETE without safety
    (r"\bDELETE\s+FROM\s+\w+(?!.*\bWHERE\b)", "DELETE FROM without WHERE"),
    # Fork bomb
    (r":\(\)\s*\{.*:\|:&\s*\};:", "fork bomb"),
    # Wide-open permissions
    (r"\bchmod\s+777\b", "chmod 777 (world-writable)"),
    # Raw device write
    (r">\s*/dev/sd[a-z]", "raw disk write"),
    # Dangerous dd
    (r"\bdd\s+if=.+\s+of=/dev/sd", "dd to raw device"),
    # Format
    (r"\bmkfs\.\w+\s+/dev/", "filesystem format"),
    # Overwrite critical files
    (r">\s*/etc/(passwd|shadow|sudoers|fstab)", "overwrite critical system file"),
]


def log_block(attempted: str, project_path: str, reason: str) -> None:
    """Append a blocked attempt to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": attempted,
        "project_path": project_path,
        "reason": reason,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command: str) -> tuple[bool, str]:
    """
    Check a command against dangerous patterns.
    Returns (is_dangerous, reason).
    """
    for pattern, description in DANGEROUS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    return False, ""


def main():
    try:
        raw = sys.stdin.buffer.read().decode("utf-8-sig")
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Not valid JSON, allow
        print(json.dumps({"continue": True}))
        return 0

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    command = ""

    # Extract the actual command from different tool formats
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "") or tool_input.get("cmd", "")
    elif isinstance(tool_input, str):
        command = tool_input

    project_path = hook_input.get("cwd", "")

    # Only intercept Bash/Run/Shell/Exec tools
    if tool_name.lower() not in ("bash", "run", "shell", "exec", "execute", "terminal"):
        print(json.dumps({"continue": True}))
        return 0

    is_dangerous, reason = check_command(command)

    if is_dangerous:
        log_block(command, project_path, reason)

        message = (
            f"BLOCKED: Detected potentially destructive command pattern.\n"
            f"  Attempted: {command}\n"
            f"  Matched pattern: {reason}\n"
            f"  Project: {project_path}\n\n"
            f"  This command has been blocked by the pre-tool-use safety hook.\n"
            f"  To proceed, please review the command manually or use a safer alternative:\n"
            f"  - Use 'trash' instead of 'rm -rf'\n"
            f"  - Add a WHERE clause with LIMIT before DELETE\n"
            f"  - Use 'git push' without --force, or rebase instead\n"
            f"  - For SQL: create a backup before DROP operations"
        )

        print(json.dumps({
            "continue": False,
            "reason": message,
        }))
        return 0

    # Safe command 鈥?allow
    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
