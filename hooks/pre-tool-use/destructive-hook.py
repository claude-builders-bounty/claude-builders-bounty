#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Install: Copy this file to ~/.claude/hooks/pre-tool-use-destroy.sh
        (Claude Code will auto-discover hooks in that directory)
        Or run: cp -r hooks/pre-tool-use ~/.claude/hooks/

The hook intercepts dangerous bash commands before they execute and:
  1. Logs every blocked attempt to ~/.claude/hooks/blocked.log
  2. Displays a clear message explaining why the command was blocked
  3. Returns non-zero exit code to prevent the command from running
"""

import sys
import os
import re
import json
import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Patterns that are ALWAYS dangerous, regardless of context
DESTRUCTIVE_PATTERNS = [
    # Recursive force remove — never safe in production, rarely safe in dev
    (r"\brm\s+-rf\s+/", "Recursive force delete of root directory"),
    (r"\brm\s+-\s*rf\s+/", "Recursive force delete of root directory"),

    # Database destruction without WHERE clause
    (r"\bDROP\s+TABLE\b", "DROP TABLE — removes entire table schema and data"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE — destroys entire database"),
    (r"\bDROP\s+SCHEMA\b", "DROP SCHEMA — removes entire schema"),

    # Git history destruction
    (r"\bgit\s+push\s+.*--force\b", "Force push — rewrites remote history, can destroy others' work"),
    (r"\bgit\s+push\s+.*-f\b", "Force push (-f flag) — rewrites remote history"),
    (r"\bgit\s+push\s+.*--delete\s+.*master\b", "Deleting master branch via push"),
    (r"\bgit\s+push\s+.*--delete\s+.*main\b", "Deleting main branch via push"),

    # Dangerous file operations
    (r"\b:()\s*\{", "Fork bomb — will crash the system"),
    (r"\bmkfs\b", "mkfs — formats a filesystem, destroying all data"),
    (r"\bdd\s+.*of=/dev/", "Direct dd to block device — can destroy disks"),

    # Shutdown/reboot (unless intentional)
    (r"\bshutdown\b.*-h\b", "System shutdown — will halt the machine"),
    (r"\bhalt\b", "System halt command"),
    (r"\bpoweroff\b", "Power off command"),
    (r"\breboot\b.*-f\b", "Force reboot without graceful shutdown"),
]

# Patterns that are dangerous ONLY when used without a WHERE clause
CONDITIONAL_DESTRUCTIVE = [
    # DELETE without WHERE — wipes data
    (r"\bDELETE\s+FROM\s+[^\s;]+(?:\s+WHERE|\s*;|\s*$|\s+ORDER\s+BY|\s+LIMIT)",
     "DELETE without WHERE clause — will delete ALL rows from the table"),
    # TRUNCATE — fast but no rollback
    (r"\bTRUNCATE\b", "TRUNCATE — removes all rows from table without logged individual deletions"),
]

# dd with of= is dangerous
DD_PATTERN = re.compile(r"\bdd\s+.*of=")


def get_project_path():
    """Get the current project path from environment or git root."""
    project = os.environ.get("CLAUDE_HOOK_PROJECT_PATH")
    if project and Path(project).exists():
        return project
    # Fallback: find git root
    try:
        result = os.popen("git rev-parse --show-toplevel 2>/dev/null").read().strip()
        if result:
            return result
    except Exception:
        pass
    return os.getcwd()


def check_command(command: str) -> list[tuple[str, str]]:
    """
    Check a command against all destructive patterns.
    Returns list of (description, pattern_name) for each match.
    """
    findings = []
    cmd_lower = command.lower()

    for pattern, description in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            findings.append((description, pattern))

    for pattern, description in CONDITIONAL_DESTRUCTIVE:
        if re.search(pattern, command, re.IGNORECASE):
            findings.append((description, pattern))

    # Special check for dd with output file
    if re.search(DD_PATTERN, command) and not re.search(r"of=/dev/zero", command):
        if re.search(r"\bof=", command):
            findings.append(("dd with output file — can overwrite disks if target is wrong", "dd of="))

    return findings


def log_blocked(timestamp: str, command: str, project: str, findings: list):
    """Append a blocked attempt to the log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    entry = (
        f"\n{'='*60}\n"
        f"Timestamp: {timestamp}\n"
        f"Project:   {project}\n"
        f"Blocked Command:\n{command}\n"
        f"Reason(s):\n" +
        "\n".join(f"  - {desc}" for desc, _ in findings) +
        f"\n{'='*60}\n"
    )

    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except Exception as e:
        print(f"[destructive-hook] Warning: could not write to log: {e}", file=sys.stderr)


def format_blocked_message(command: str, findings: list, project: str) -> str:
    """Format the error message shown to Claude when a command is blocked."""
    reasons = "\n".join(f"  • {desc}" for desc, _ in findings)

    return f"""
🚫 COMMAND BLOCKED — DESTRUCTIVE OPERATION DETECTED

The following command was blocked by the pre-tool-use hook:

  {command}

Located in: {project}

Reason(s):
{reasons}

This command cannot be executed because it poses an unacceptable risk
of permanent data loss or damage to shared resources.

If you intentionally need to run this operation:
  1. Disable the hook temporarily: Claude Code settings → hooks → disabled
  2. Run your command with extreme caution
  3. Re-enable the hook afterward

All blocked attempts are logged to: {LOG_FILE}
"""


def main():
    """Main entry point — reads Claude Code hook JSON from stdin."""
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            # No input — allow the tool to run
            sys.exit(0)

        # Claude Code passes tool input as JSON
        try:
            data = json.loads(raw_input)
        except json.JSONDecodeError:
            # Not JSON — allow
            sys.exit(0)

        # Extract the bash command
        command = ""
        tool_name = data.get("tool", "") if isinstance(data, dict) else ""

        if tool_name == "Bash":
            if isinstance(data, dict):
                command = data.get("command", "") or data.get("cmd", "") or ""
            elif isinstance(data, str):
                command = data
        elif "command" in data:
            command = data["command"]
        elif "cmd" in data:
            command = data["cmd"]

        if not command or not isinstance(command, str):
            sys.exit(0)

        command = command.strip()
        if not command:
            sys.exit(0)

        project = get_project_path()
        findings = check_command(command)

        if findings:
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            log_blocked(timestamp, command, project, findings)
            msg = format_blocked_message(command, findings, project)
            print(msg, file=sys.stderr)
            sys.exit(1)  # Non-zero = block the tool

        sys.exit(0)  # Allow

    except Exception as e:
        # On error, allow the command (fail open — don't block due to hook bugs)
        print(f"[destructive-hook] Warning: hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
