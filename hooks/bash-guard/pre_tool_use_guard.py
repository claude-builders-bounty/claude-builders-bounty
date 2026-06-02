#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Command Guard

Intercepts dangerous bash commands before execution. Blocks patterns like:
  rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM (without WHERE)

Installation:
  1. Copy this file to ~/.claude/hooks/pre-tool-use-guard.py
  2. Add to ~/.claude/settings.json:
     {
       "hooks": {
         "preToolUse": [{
           "matcher": "Bash",
           "command": "python3 ~/.claude/hooks/pre-tool-use-guard.py"
         }]
       }
     }

Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ─── Configuration ───────────────────────────────────────────────────────────

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# ─── Destructive Patterns ────────────────────────────────────────────────────
# Each entry: (compiled_regex, description, severity)
# severity: "critical" = always block, "warning" = block but explain

DESTRUCTIVE_PATTERNS = [
    # rm -rf / rm -fr — recursive force delete
    (
        re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b"),
        "Recursive force delete (rm -rf) — can destroy entire directories",
        "critical",
    ),
    (
        re.compile(r"\brm\s+(-[a-zA-Z]*f)\s+[/~]"),
        "Force delete from root/home — dangerous system-level operation",
        "critical",
    ),
    # DROP TABLE / DROP DATABASE
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE — permanently removes table and all data",
        "critical",
    ),
    (
        re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE),
        "DROP DATABASE — permanently removes entire database",
        "critical",
    ),
    # TRUNCATE
    (
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE — deletes all rows without logging, cannot rollback easily",
        "critical",
    ),
    # DELETE FROM without WHERE clause
    (
        re.compile(r"\bDELETE\s+FROM\b(?!.+\bWHERE\b)", re.IGNORECASE),
        "DELETE FROM without WHERE — deletes ALL rows from table",
        "critical",
    ),
    # git push --force (but allow --force-with-lease)
    (
        re.compile(r"\bgit\s+push\b.+(--force(?!-with-lease)|(?<!\w)-f\b)"),
        "Force push — overwrites remote history, can lose others' work",
        "warning",
    ),
    # git reset --hard on main/master/production
    (
        re.compile(r"\bgit\s+reset\s+--hard\b.+\b(main|master|production|release)\b"),
        "Hard reset on protected branch — destroys commit history",
        "critical",
    ),
    # chmod 777 — overly permissive
    (
        re.compile(r"\bchmod\s+777\b"),
        "chmod 777 — gives everyone full read/write/execute permissions",
        "warning",
    ),
    # curl | sh / curl | bash — pipe to shell
    (
        re.compile(r"\bcurl\b.+\|\s*(ba)?sh\b"),
        "Pipe remote script to shell — executes untrusted code directly",
        "warning",
    ),
    # mkfs — format filesystem
    (
        re.compile(r"\bmkfs\b"),
        "mkfs — formats a filesystem, destroys all data on target",
        "critical",
    ),
    # dd with of=/dev — raw disk write
    (
        re.compile(r"\bdd\b.+\bof=/dev/"),
        "dd to device — raw disk write, can destroy partition table",
        "critical",
    ),
    # :(){ :|:& };: — fork bomb
    (
        re.compile(r":\(\)\s*\{\s*:\|\:\&\s*\}\s*;:"),
        "Fork bomb — spawns infinite processes, crashes system",
        "critical",
    ),
    # > /dev/sda — overwrite disk
    (
        re.compile(r">\s*/dev/sd[a-z]"),
        "Overwrite block device — corrupts disk directly",
        "critical",
    ),
    # nc -e / netcat reverse shell
    (
        re.compile(r"\bnc\b.+-e\s+/bin/(ba)?sh"),
        "Netcat reverse shell — opens remote access to system",
        "critical",
    ),
]


# ─── Helper Functions ────────────────────────────────────────────────────────

def log_blocked_attempt(command: str, project_path: str, reason: str, severity: str):
    """Log the blocked attempt to the log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = (
        f"[{timestamp}] [{severity.upper()}] BLOCKED\n"
        f"  Command: {command}\n"
        f"  Project: {project_path}\n"
        f"  Reason:  {reason}\n"
        f"{'─' * 60}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[str, str] | None:
    """
    Check command against destructive patterns.
    Returns (reason, severity) if blocked, None if safe.
    """
    for pattern, reason, severity in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return reason, severity
    return None


def extract_command(tool_input: dict) -> str | None:
    """Extract the bash command from the tool input."""
    # Claude Code passes tool input as {"command": "...", ...}
    cmd = tool_input.get("command", "")
    if not cmd:
        return None
    return cmd


# ─── Main Hook Logic ─────────────────────────────────────────────────────────

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # Can't parse input — let it through (fail open for non-bash tools)
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only intercept Bash tool
    if tool_name != "Bash":
        sys.exit(0)

    command = extract_command(tool_input)
    if not command:
        sys.exit(0)

    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    result = check_command(command)
    if result:
        reason, severity = result
        log_blocked_attempt(command, project_path, reason, severity)

        # Output message to Claude (shown in the conversation)
        msg = (
            f"🚫 **Command BLOCKED by bash-guard hook**\n\n"
            f"**Command:** `{command}`\n"
            f"**Reason:** {reason}\n\n"
            f"This command matches a destructive pattern and was blocked "
            f"to prevent accidental data loss. If this is intentional, "
            f"please run it manually in your terminal."
        )
        print(msg, file=sys.stderr)
        sys.exit(2)  # non-zero = block the tool

    # Command is safe — allow
    sys.exit(0)


if __name__ == "__main__":
    main()
