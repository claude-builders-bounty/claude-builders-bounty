#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook — Destructive Command Guard
Blocks dangerous bash commands before execution.

Installation:
  cp destructive-guard.py ~/.claude/hooks/pre-tool-use
  chmod +x ~/.claude/hooks/pre-tool-use

Claude Code calls this hook with JSON on stdin before every tool use.
If exit code != 0, the tool call is rejected.
"""

import json
import re
import sys
import os
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that are ALWAYS blocked (case-insensitive)
BLOCK_PATTERNS = [
    # File system destruction
    r"rm\s+-[a-z]*r[a-z]*f[a-z]*\b",
    r"rm\s+-[a-z]*f[a-z]*r[a-z]*\b",
    r"rm\s+-r\s+-f\b",
    r"rm\s+-f\s+-r\b",
    r"sudo\s+rm\b",
    r":\s*\(\)\s*\{\s*:\s*\|\:\s*\}\s*;\s*:",  # fork bomb
    r"mkfs\.",
    r"dd\s+if=",
    r">\s*/dev/sd[a-z]",
    # Database destruction
    r"\bdrop\s+table\b",
    r"\bdrop\s+database\b",
    r"\btruncate\s+(table\s+)?\w",
    # Dangerous git operations
    r"git\s+push\s+.*--force\b",
    r"git\s+push\s+.*-f\b",
    r"git\s+reset\s+--hard\b",
    r"git\s+clean\s+-[a-z]*f",
    # SQL injection patterns
    r"\bdelete\s+from\s+\w+\s*(?!.*\bwhere\b)",
    # System takeover
    r"chmod\s+777\b",
    r"chmod\s+-R\s+777\b",
    r"chown\s+-R\b",
    # Nuclear options
    r"shutdown\b",
    r"reboot\b",
    r"halt\b",
    r"poweroff\b",
]

# Patterns that require a WHERE clause for DELETE/DROP (checked separately)
REQUIRE_WHERE_PATTERNS = [
    (r"\bdelete\s+from\s+(\w+)", "DELETE FROM requires a WHERE clause"),
    (r"\bupdate\s+(\w+)\s+set\b", "UPDATE without WHERE is dangerous — add WHERE or confirm"),
]

# ── Logic ──────────────────────────────────────────────────

def get_project_path(stdin_data: dict) -> str:
    """Extract working directory from hook input."""
    return stdin_data.get("cwd", "")


def log_block(command: str, pattern: str, project: str) -> None:
    """Log blocked attempt to file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | project={project} | pattern={pattern} | command={command}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    Returns (blocked: bool, reason: str).
    """
    cmd_lower = command.lower()

    # 1. Check always-blocked patterns
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, cmd_lower):
            return True, f"Matched dangerous pattern: {pattern}"

    # 2. Check DELETE/UPDATE without WHERE
    for pattern, reason in REQUIRE_WHERE_PATTERNS:
        match = re.search(pattern, cmd_lower)
        if match:
            # Look ahead in the command for WHERE clause
            after_match = cmd_lower[match.end():]
            if "where" not in after_match:
                return True, reason

    return False, ""


def format_block_message(command: str, reason: str) -> str:
    """Build a human-readable rejection message."""
    return f"""
╔══════════════════════════════════════════════════════════╗
║  🛑  DESTRUCTIVE COMMAND BLOCKED                        ║
╠══════════════════════════════════════════════════════════╣
║  Command: {command[:50]:<50} ║
║  Reason:  {reason[:50]:<50} ║
╠══════════════════════════════════════════════════════════╣
║  This command was intercepted by the Destructive Guard   ║
║  pre-tool-use hook. If you're sure this is safe, use     ║
║  a safer alternative (e.g., rm -i, git push without      ║
║  --force, DELETE with WHERE clause).                     ║
║                                                          ║
║  Logged to: ~/.claude/hooks/blocked.log                  ║
╚══════════════════════════════════════════════════════════╝
"""


def main():
    try:
        stdin_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No input or invalid — allow by default
        sys.exit(0)

    # Only intercept bash tool calls
    tool_name = stdin_data.get("tool_name", "")
    if tool_name.lower() != "bash":
        sys.exit(0)

    tool_input = stdin_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)

    if blocked:
        project = get_project_path(stdin_data)
        log_block(command, reason, project)
        print(format_block_message(command, reason), file=sys.stderr)
        sys.exit(1)  # Non-zero exit = reject the tool call

    sys.exit(0)  # Zero exit = allow


if __name__ == "__main__":
    main()
