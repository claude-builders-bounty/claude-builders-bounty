#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

Intercepts dangerous patterns like `rm -rf`, `DROP TABLE`, `git push --force`,
`TRUNCATE`, `DELETE FROM` without WHERE, and more.

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

BLOCKED_PATTERNS = [
    # File system destruction
    (r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*|.*--force)\b", "rm with --force detected"),
    (r"\brm\s+-[^\s]*r[^\s]*f", "rm -rf detected"),
    (r"\bshred\b", "shred command detected"),
    (r"\bdd\s+.*of=/dev/", "dd writing to device detected"),
    (r"\bmkfs\b", "mkfs (format) command detected"),
    (r"\bswapoff\b.*\|\s*swapon", "swap reset detected"),
    # Database destruction
    (r"\bDROP\s+TABLE\b", "DROP TABLE detected"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE detected"),
    (r"\bDROP\s+SCHEMA\b", "DROP SCHEMA detected"),
    (r"\bTRUNCATE\b", "TRUNCATE detected"),
    (r"\bDELETE\s+FROM\b(?!\s+.*\bWHERE\b)", "DELETE FROM without WHERE clause detected"),
    (r"\bALTER\s+TABLE\b.*\bDROP\b", "ALTER TABLE ... DROP detected"),
    (r"\bDROP\s+INDEX\b", "DROP INDEX detected"),
    # Git destruction
    (r"\bgit\s+push\s+(-[^\s]*f[^\s]*|.*--force)", "git push --force detected"),
    (r"\bgit\s+push\s+(-[^\s]*f[^\s]*|.*--force)\s+--all", "git push --force --all detected"),
    (r"\bgit\s+clean\s+(-[^\s]*f[^\s]*|.*--force)", "git clean --force detected"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard detected"),
    (r"\bgit\s+branch\s+(-[^\s]*D[^\s]*|.*--delete)\s+(main|master)", "deleting main/master branch"),
    # System destruction
    (r"\bkill\s+(-[^\s]*9[^\s]*|.*SIGKILL)\s+[1-9]", "kill -9 on system process"),
    (r"\bsystemctl\s+(stop|disable|mask)\b", "systemctl stop/disable/mask detected"),
    (r"\bshutdown\b", "shutdown command detected"),
    (r"\breboot\b", "reboot command detected"),
    (r"\bpoweroff\b", "poweroff command detected"),
    (r"\bchmod\s+(-R\s+)?777\b", "chmod 777 detected"),
    (r"\b>.*(/dev/sd|/dev/nvme|/dev/mmc|/dev/vd)", "direct write to block device"),
    (r"\bcurl\b.*\|\s*bash", "piping curl directly to bash"),
    (r"\bwget\b.*\|\s*(ba)?sh", "piping wget directly to shell"),
]

# Commands that are always allowed (false positive suppression)
ALLOWED_CONTEXTS = [
    r"echo\s+.*",           # echo commands are safe
    r"#.*",                 # comments
    r".*--dry-run.*",       # dry runs are safe
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# ── Core Logic ─────────────────────────────────────────────────────────────────


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches any blocked pattern.

    Returns:
        (is_blocked, reason) tuple
    """
    # Normalize the command for checking
    normalized = command.strip()

    # Check if it's in an allowed context
    for pattern in ALLOWED_CONTEXTS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return False, ""

    # Check blocked patterns
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, reason

    return False, ""


def log_blocked_attempt(tool_name: str, command: str, reason: str, cwd: str = "") -> None:
    """Log a blocked command attempt to the log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  tool: {tool_name}\n"
        f"  reason: {reason}\n"
        f"  command: {command}\n"
        f"  cwd: {cwd}\n"
        f"---\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def main():
    """Main entry point for the Claude Code hook.

    Reads hook input from stdin, decides whether to block, writes decision to stdout.
    """
    # Read hook input from Claude Code
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept Bash tool calls
    if tool_name != "Bash":
        # Allow all non-Bash tools
        output = {"decision": "allow", "reason": ""}
        print(json.dumps(output))
        return

    command = tool_input.get("command", "")
    cwd = os.getcwd()

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked_attempt(tool_name, command, reason, cwd)
        output = {
            "decision": "block",
            "reason": (
                f"BLOCKED: {reason}\n\n"
                f"This command was blocked by the pre-tool-use safety hook.\n"
                f"Command: {command}\n\n"
                f"If this is intentional, the user can override by running\n"
                f"the command directly in their terminal."
            ),
        }
    else:
        output = {"decision": "allow", "reason": ""}

    print(json.dumps(output))


if __name__ == "__main__":
    main()
