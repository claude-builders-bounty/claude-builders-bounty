#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Install: copy to ~/.claude/hooks/destructive_bash_hook.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Patterns that are unconditionally blocked
BLOCK_PATTERNS = [
    (r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*)\b", "rm -rf (recursive force delete)"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE (destructive SQL)"),
    (r"\bTRUNCATE\b", "TRUNCATE (destructive SQL)"),
    (r"\bgit\s+push\s+.*--force\b", "git push --force (force push)"),
    (r"\bgit\s+push\s+.*-f\b", "git push -f (force push)"),
    # DELETE FROM without a WHERE clause (allow DELETE FROM ... WHERE ...)
    (r"\bDELETE\s+FROM\s+\w+\s*(?:;|$)", "DELETE FROM without WHERE clause"),
]


def check_command(cmd: str) -> tuple[bool, str]:
    """Returns (should_block, reason). Case-insensitive for SQL patterns."""
    for pattern, label in BLOCK_PATTERNS:
        flags = re.IGNORECASE if any(kw in label for kw in ("SQL", "DELETE", "DROP", "TRUNCATE")) else 0
        if re.search(pattern, cmd, flags):
            return True, label
    return False, ""


def log_blocked(cmd: str, reason: str, project_path: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] BLOCKED | reason={reason!r} | project={project_path!r} | cmd={cmd!r}\n"
    with LOG_FILE.open("a") as f:
        f.write(entry)


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Not a valid hook event — allow through
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)  # Only inspect Bash tool calls

    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Session context (may not always be present)
    project_path = event.get("cwd") or event.get("project_path") or "unknown"

    should_block, reason = check_command(command)

    if should_block:
        log_blocked(command, reason, project_path)
        output = {
            "decision": "block",
            "reason": (
                f"Blocked by destructive-bash-hook: {reason}. "
                f"This command pattern is not allowed because it can cause irreversible damage. "
                f"Attempt logged to {LOG_FILE}."
            ),
        }
        print(json.dumps(output))
        sys.exit(0)

    # Allow all other commands silently
    sys.exit(0)


if __name__ == "__main__":
    main()
