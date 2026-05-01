#!/usr/bin/env python3
"""
Pre-Tool-Use Hook: Dangerous Command Interceptor for Claude Code

Intercepts and blocks destructive bash commands before execution.
Covers: rm -rf, DROP TABLE, TRUNCATE, DELETE FROM (no WHERE), git push --force,
        mkfs, fork bombs, disk wipes, reverse shells, and more.

Logs every blocked attempt to ~/.claude/hooks/blocked.log with:
  - Timestamp, attempted command, project path

Usage:
  1. cp hook-safety.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/hook-safety.py
  2. Add to ~/.claude/settings.json (see README)

Exit codes:
  0 + no stdout   → allow
  0 + JSON stdout → block (Claude reads the reason)
  non-zero        → block (safety measure)
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── Log Configuration ────────────────────────────────────────────────────────

LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

# ─── Dangerous Command Patterns ───────────────────────────────────────────────

DANGEROUS_PATTERNS = [
    # ── Critical: Data Destruction ──
    {
        "pattern": r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force)\s+/",
        "description": "Recursive force delete from root filesystem",
        "severity": "critical",
    },
    {
        "pattern": r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*r|--force\s+--recursive)\s+/",
        "description": "Recursive force delete from root filesystem (flag order variant)",
        "severity": "critical",
    },
    {
        "pattern": r"\brm\s+-rf\s+~/",
        "description": "Recursive force delete of home directory",
        "severity": "critical",
    },
    {
        "pattern": r"\brm\s+-rf\s+\*",
        "description": "Recursive force delete with wildcard",
        "severity": "critical",
    },
    {
        "pattern": r"\brm\s+-rf\s+\.",
        "description": "Recursive force delete of current directory",
        "severity": "critical",
    },
    {
        "pattern": r"\bmkfs\b",
        "description": "Filesystem format command",
        "severity": "critical",
    },
    {
        "pattern": r"\bfdisk\b.*\b/dev/",
        "description": "Disk partition manipulation",
        "severity": "critical",
    },
    {
        "pattern": r"\bdd\s+.*if=/dev/(zero|urandom|random)",
        "description": "Writing random/zero data to device (potential disk wipe)",
        "severity": "critical",
    },
    {
        "pattern": r":(){ :\|:& };:",
        "description": "Fork bomb",
        "severity": "critical",
    },
    {
        "pattern": r"\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b",
        "description": "System shutdown/reboot command",
        "severity": "critical",
    },

    # ── Critical: SQL Destruction ──
    {
        "pattern": r"\bDROP\s+TABLE\b",
        "description": "DROP TABLE — permanently deletes a table and all its data",
        "severity": "critical",
    },
    {
        "pattern": r"\bDROP\s+DATABASE\b",
        "description": "DROP DATABASE — permanently deletes an entire database",
        "severity": "critical",
    },
    {
        "pattern": r"\bTRUNCATE\s+TABLE\b",
        "description": "TRUNCATE TABLE — removes all rows without logging individual deletes",
        "severity": "critical",
    },
    {
        "pattern": r"\bTRUNCATE\b",
        "description": "TRUNCATE — removes all rows from a table",
        "severity": "critical",
    },
    {
        "pattern": r"\bDELETE\s+FROM\b(?!\s+\S+\s+WHERE\b)",
        "description": "DELETE FROM without WHERE clause — deletes all rows",
        "severity": "critical",
    },

    # ── High: Dangerous File Operations ──
    {
        "pattern": r"\brm\s+(-[a-zA-Z]*r|--recursive)\s+/",
        "description": "Recursive delete from absolute path (no --force but still dangerous)",
        "severity": "high",
    },
    {
        "pattern": r"\bchmod\s+(-R\s+)?777\s+/",
        "description": "Setting world-writable permissions on system directories",
        "severity": "high",
    },
    {
        "pattern": r"\bchown\s+.*\s+/",
        "description": "Changing ownership of root-level files",
        "severity": "high",
    },
    {
        "pattern": r">\s*/dev/sd[a-z]",
        "description": "Redirecting output to raw disk device",
        "severity": "high",
    },
    {
        "pattern": r"\bcurl\b.*\|\s*(ba)?sh",
        "description": "Piping curl output directly to shell (remote code execution)",
        "severity": "high",
    },
    {
        "pattern": r"\bwget\b.*\|\s*(ba)?sh",
        "description": "Piping wget output directly to shell (remote code execution)",
        "severity": "high",
    },
    {
        "pattern": r"\bnc\s+.*-e\s*/bin/(ba)?sh",
        "description": "Netcat reverse shell",
        "severity": "high",
    },
    {
        "pattern": r"\biptables\s+-F",
        "description": "Flushing all firewall rules",
        "severity": "high",
    },
    {
        "pattern": r"\bgit\s+push\s+.*--force\b",
        "description": "Force push to git remote — can destroy remote history",
        "severity": "high",
    },

    # ── Medium: Potentially Risky ──
    {
        "pattern": r"\bgit\s+reset\s+--hard\b",
        "description": "Hard git reset (uncommitted changes lost)",
        "severity": "medium",
    },
    {
        "pattern": r"\bgit\s+clean\s+.*-f",
        "description": "Force clean untracked files",
        "severity": "medium",
    },
    {
        "pattern": r"\bnpm\s+publish\b",
        "description": "Publishing package to npm registry",
        "severity": "medium",
    },
    {
        "pattern": r"\bpip\s+install\s+.*--break-system-packages",
        "description": "Installing Python packages bypassing system protection",
        "severity": "medium",
    },
]

# Severity levels that trigger blocking
BLOCK_SEVERITIES = {"critical", "high"}
WARN_SEVERITIES = {"medium"}

SEVERITY_EMOJI = {
    "critical": "🚨",
    "high": "⚠️",
    "medium": "⚡",
}


# ─── Logging ──────────────────────────────────────────────────────────────────

def log_blocked_attempt(command: str, rule: dict, project_path: str) -> None:
    """Append a blocked attempt to the log file."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"[{timestamp}] "
            f"SEVERITY={rule['severity']} "
            f"RULE={rule['description']} "
            f"PROJECT={project_path}\n"
            f"  COMMAND: {command}\n"
        )
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except OSError:
        # Logging failure should not prevent blocking
        pass


# ─── Command Extraction ──────────────────────────────────────────────────────

def extract_command(input_data: dict) -> Optional[str]:
    """Extract the shell command from Claude's tool input."""
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        command = input_data.get("command", "")
    return command if isinstance(command, str) else None


def get_project_path(input_data: dict) -> str:
    """Extract the project/workspace path from input or environment."""
    # Try to get from tool input
    tool_input = input_data.get("tool_input", {})
    for key in ("cwd", "path", "directory"):
        if key in tool_input:
            return str(tool_input[key])
    # Fall back to environment
    return os.environ.get("PWD", os.getcwd())


# ─── Pattern Matching ─────────────────────────────────────────────────────────

def check_dangerous_patterns(command: str) -> Optional[dict]:
    """Check command against dangerous patterns. Returns first match or None."""
    for rule in DANGEROUS_PATTERNS:
        if re.search(rule["pattern"], command, re.IGNORECASE):
            return rule
    return None


# ─── Response Formatting ──────────────────────────────────────────────────────

def format_block_response(rule: dict, command: str) -> dict:
    """Format a block response with explanation."""
    emoji = SEVERITY_EMOJI.get(rule["severity"], "❓")

    reason = (
        f"{emoji} BLOCKED [{rule['severity'].upper()}]: {rule['description']}\n\n"
        f"Command: {command}\n\n"
        f"This command was intercepted by the pre-tool-use safety hook.\n"
        f"Severity: {rule['severity']}\n"
        f"Rule: {rule['description']}\n\n"
        f"If you believe this command is safe and necessary, you can:\n"
        f"  1. Modify the command to be less destructive\n"
        f"  2. Temporarily disable the hook in your Claude settings\n"
        f"  3. Run the command manually with proper precautions"
    )

    return {
        "decision": "block",
        "reason": reason,
        "severity": rule["severity"],
        "rule": rule["description"],
    }


def format_warn_response(rule: dict, command: str) -> dict:
    """Format a warning response (block with softer language)."""
    reason = (
        f"⚡ WARNING [{rule['severity'].upper()}]: {rule['description']}\n\n"
        f"Command: {command}\n\n"
        f"This command was flagged by the safety hook but may be intentional.\n"
        f"Please verify this is what you want to do."
    )

    return {
        "decision": "block",
        "reason": reason,
        "severity": rule["severity"],
        "rule": rule["description"],
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Main hook entry point."""
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            sys.exit(0)

        input_data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    command = extract_command(input_data)
    if not command:
        sys.exit(0)

    rule = check_dangerous_patterns(command)

    if rule is None:
        # Safe — allow
        sys.exit(0)

    # Log the blocked attempt
    project_path = get_project_path(input_data)
    log_blocked_attempt(command, rule, project_path)

    # Build response
    if rule["severity"] in BLOCK_SEVERITIES:
        response = format_block_response(rule, command)
    elif rule["severity"] in WARN_SEVERITIES:
        response = format_warn_response(rule, command)
    else:
        response = format_block_response(rule, command)

    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
