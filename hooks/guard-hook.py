#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook — Dangerous Command Blocker

Intercepts Bash tool calls before execution and blocks known-dangerous patterns.
Designed for the claude-builders-bounty #3 Hook bounty ($100).

Blocked patterns:
  - rm -rf (and variants like rm -r, rm --recursive --force)
  - DROP TABLE / DROP DATABASE
  - git push --force / --force-with-lease (on main/master)
  - TRUNCATE TABLE
  - DELETE FROM without WHERE clause
  - curl | bash / wget | sh (pipe-to-shell)
  - chmod 777 / chown -R on system paths
  - :(){ :|:& };: (fork bomb)
  - mkfs.* / dd to disk devices

Hook protocol (per Claude Code docs):
  - Receives JSON on stdin: {tool_name, tool_input, cwd, ...}
  - Exit 0 = allow the tool call
  - Exit 2 = block the tool call (stderr message shown to Claude)
  - Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---- Configuration ----
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

# ---- Dangerous Pattern Definitions ----
# Each entry: (pattern, description, severity)
# Patterns are regex applied to the full command string (case-insensitive for SQL)

DANGEROUS_PATTERNS: list[tuple[str, str, str]] = [
    # Destructive file operations
    (
        r'\brm\s+(?:\s*-(?:-?\s*)?[rRf]+[a-zA-Z]*\s+)+\S',
        "rm with recursive/force flags — dangerous file deletion",
        "CRITICAL",
    ),
    (
        r'\brm\s+.*-rf\b',
        "rm -rf — recursive forced removal",
        "CRITICAL",
    ),
    (
        r'\bfind\b.*\b-delete\b',
        "find ... -delete — bulk file deletion",
        "HIGH",
    ),
    (
        r'\bdd\s+if=.*\bof=/dev/',
        "dd writing to a disk device — can destroy filesystems",
        "CRITICAL",
    ),
    (
        r'\bmkfs\.',
        "mkfs — filesystem creation (destroys existing data)",
        "CRITICAL",
    ),

    # Dangerous SQL
    (
        r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b',
        "DROP TABLE/DATABASE/SCHEMA — irreversible schema destruction",
        "CRITICAL",
    ),
    (
        r'\bTRUNCATE\s+(TABLE\s+)?',
        "TRUNCATE TABLE — deletes all rows, cannot rollback in some engines",
        "CRITICAL",
    ),
    (
        r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)',
        "DELETE FROM without WHERE clause — deletes all rows",
        "CRITICAL",
    ),

    # Dangerous git operations
    (
        r'\bgit\s+push\s+(?:--force|-[fF]\b)',
        "git push --force — overwrites remote history",
        "HIGH",
    ),
    (
        r'\bgit\s+push\s+.*--force-with-lease\b',
        "git push --force-with-lease — overwrites remote history",
        "MEDIUM",
    ),
    (
        r'\bgit\s+push\s+--delete\b',
        "git push --delete — deletes remote branch",
        "HIGH",
    ),

    # Pipe-to-shell (remote code execution)
    (
        r'\bcurl\s+\S+.*\|\s*(?:sudo\s+)?(?:ba)?sh\b',
        "curl | bash — executing remote script directly",
        "CRITICAL",
    ),
    (
        r'\bwget\s+\S+.*\|\s*(?:sudo\s+)?(?:ba)?sh\b',
        "wget | sh — executing remote script directly",
        "CRITICAL",
    ),
    (
        r'\bcurl\s+\S+.*\|\s*(?:sudo\s+)?python\d*\b',
        "curl | python — executing remote Python code directly",
        "CRITICAL",
    ),

    # Permission escalation
    (
        r'\bchmod\s+(?:-R\s+)?777\b',
        "chmod 777 — world-writable permissions on everything",
        "HIGH",
    ),
    (
        r'\bchown\s+-R\s+\S+\s+/\S*',
        "chown -R on root-level path — recursive ownership change",
        "CRITICAL",
    ),

    # Fork bombs / DoS
    (
        r':\(\)\s*\{[^}]*:\|:&\s*\}[^}]*;?\s*:',
        "fork bomb — will crash the system",
        "CRITICAL",
    ),
    (
        r'\bperl\s+-e\s+.*fork\b',
        "perl fork bomb variant",
        "CRITICAL",
    ),

    # System destructive
    (
        r'\b(?:halt|shutdown|reboot|poweroff)\b',
        "system halt/reboot command",
        "HIGH",
    ),
]


def load_hook_input() -> dict:
    """Read JSON hook input from stdin."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return {}


def check_dangerous(command: str) -> list[dict]:
    """
    Check a command against all dangerous patterns.
    Returns list of matched patterns with details.
    """
    matches = []
    for pattern, description, severity in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            matches.append({
                "pattern": pattern,
                "description": description,
                "severity": severity,
            })
    return matches


def log_blocked(command: str, cwd: str, matches: list[dict]) -> None:
    """Log a blocked command attempt to the log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": cwd,
        "matched_rules": [m["description"] for m in matches],
        "severity": max((m["severity"] for m in matches), key=lambda s: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(s)),
    }

    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        # Fallback: write to stderr if we can't log
        print(f"[WARN] Could not write to log file: {LOG_FILE}", file=sys.stderr)


def format_block_message(command: str, matches: list[dict]) -> str:
    """Format a human-readable block message for Claude."""
    lines = [
        "=" * 60,
        "🛡️  DANGEROUS COMMAND BLOCKED",
        "=" * 60,
        "",
        f"Command:  {command}",
        "",
        "Matched dangerous pattern(s):",
    ]
    for i, m in enumerate(matches, 1):
        lines.append(f"  {i}. [{m['severity']}] {m['description']}")

    lines.extend([
        "",
        "This command was intercepted by the PreToolUse security hook.",
        "If you believe this is a false positive, you can:",
        "  1. Review the command carefully",
        "  2. Run it manually in a separate terminal",
        "  3. Temporarily disable the hook (not recommended)",
        "  4. Ask the user for explicit confirmation",
        "",
        f"Log entry written to: {LOG_FILE}",
        "=" * 60,
    ])
    return "\n".join(lines)


def main():
    # Load hook input from stdin
    hook_input = load_hook_input()

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    cwd = hook_input.get("cwd", os.getcwd())

    # Only intercept Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")

    # Skip empty commands
    if not command.strip():
        sys.exit(0)

    # Check against dangerous patterns
    matches = check_dangerous(command)

    if not matches:
        # Command is safe — allow it
        sys.exit(0)

    # Command matched dangerous patterns — block it
    log_blocked(command, cwd, matches)

    # Write block message to stderr (Claude Code displays this)
    block_message = format_block_message(command, matches)
    print(block_message, file=sys.stderr)

    # Exit code 2 = block the tool call
    sys.exit(2)


if __name__ == "__main__":
    main()
