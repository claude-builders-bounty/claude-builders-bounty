#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands before execution.

Blocks dangerous patterns like rm -rf, DROP TABLE, git push --force,
TRUNCATE, and DELETE FROM without a WHERE clause.

Logs every blocked attempt to ~/.claude/hooks/blocked.log

Installation: see README.md in this directory.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
BLOCKED_LOG = os.path.join(HOOKS_DIR, "blocked.log")

# ---------------------------------------------------------------------------
# Pattern definitions – each tuple is (pattern, human-readable label)
# ---------------------------------------------------------------------------
DANGEROUS_PATTERNS = [
    # Filesystem destruction
    (
        r'\brm\s+.*-r.*f\b',
        "rm -rf (recursive force removal) — irreversible filesystem deletion"
    ),
    (
        r'\brm\s+.*-f.*r\b',
        "rm -rf (recursive force removal) — irreversible filesystem deletion"
    ),
    (
        r'\brm\s+-rf\b',
        "rm -rf (recursive force removal) — irreversible filesystem deletion"
    ),
    (
        r'\brm\s+-fr\b',
        "rm -fr (force recursive removal) — irreversible filesystem deletion"
    ),
    (
        r'\brm\s+.*--no-preserve-root\b',
        "rm --no-preserve-root — can delete the entire filesystem"
    ),
    (
        r'\bdd\s+if=.*of=/dev/sd[a-z]',
        "dd overwriting block device — irreversible disk destruction"
    ),
    (
        r'>\s*/dev/sda',
        "redirect overwriting /dev/sda — irreversible disk destruction"
    ),

    # Database destruction
    (
        r'\bDROP\s+TABLE\b',
        "DROP TABLE — permanently deletes a database table and all its data",
    ),
    (
        r'\bDROP\s+DATABASE\b',
        "DROP DATABASE — permanently deletes an entire database",
    ),
    (
        r'\bTRUNCATE\s+(TABLE\s+)?',
        "TRUNCATE — removes all rows from a table without possibility of rollback",
    ),
    (
        r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)',
        "DELETE FROM without WHERE — would delete every row in the table",
    ),

    # Git force-push
    (
        r'\bgit\s+push\s+.*--force(?!-with-lease)\b',
        "git push --force — overwrites remote history, potentially losing others' work",
    ),
    (
        r'\bgit\s+push\s+-[fF](?!\S)',
        "git push -f — force push shorthand, same risk as --force",
    ),

    # Destructive chmod/chown
    (
        r'\bchmod\s+(-R\s+)?777\s+/',
        "chmod 777 on root-level path — world-writable system files",
    ),
    (
        r'\bchown\s+(-R\s+)?.*:.*\s+/',
        "chown on root-level path — changes ownership of system files",
    ),

    # Fork bomb
    (
        r':\(\)\s*\{',
        "fork bomb pattern — will exhaust system resources",
    ),
]

# Pattern that is logged (warned) but NOT blocked
WARN_PATTERNS = [
    (
        r'\bgit\s+push\s+--force-with-lease\b',
        "git push --force-with-lease (safer force-push variant)",
    ),
]


def log_event(level: str, command: str, details: str) -> None:
    """Append a structured log entry."""
    os.makedirs(HOOKS_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cwd = os.getcwd()
    entry = {
        "timestamp": timestamp,
        "level": level,
        "command": command,
        "details": details,
        "project_path": cwd,
    }
    with open(BLOCKED_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command: str) -> tuple[bool, list[str]]:
    """
    Returns (should_block, list_of_reasons).
    """
    reasons = []
    for pattern, label in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            reasons.append(label)

    # Also check warn-only patterns (logged but not blocked)
    for pattern, label in WARN_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_event("WARN", command, f"Pattern matched (warn-only): {label}")

    return len(reasons) > 0, reasons


def format_blocked_message(command: str, reasons: list[str]) -> str:
    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║  ⛔ BLOCKED: Destructive command prevented by safety hook  ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
        f"  Command:  {command}",
        "",
        "  Reason(s):",
    ]
    for r in reasons:
        lines.append(f"    • {r}")
    lines.extend([
        "",
        "  ────────────────────────────────────────────────────────────",
        "  This command was blocked to prevent accidental data loss or",
        "  system damage. If you are CERTAIN this command is safe and",
        "  intentional, run it manually in a terminal outside Claude Code.",
        "",
        f"  Attempt logged to: {BLOCKED_LOG}",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    # Read the hook input from stdin (Claude Code passes JSON)
    raw = sys.stdin.read()
    if not raw.strip():
        # No input — nothing to check
        sys.exit(0)

    try:
        hook_input = json.loads(raw)
    except json.JSONDecodeError:
        # Can't parse — allow through (fail-open for safety)
        sys.exit(0)

    # Extract the command from the tool input.
    # Claude Code hook format provides tool_name and tool_input.
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only check bash/terminal commands
    if tool_name not in ("Bash", "bash", "RunShellCommand", "execute_command"):
        # Not a command execution — allow
        sys.exit(0)

    # Extract command string (can be in different fields)
    command = tool_input.get("command", "") or tool_input.get("cmd", "") or ""

    if not command:
        sys.exit(0)

    should_block, reasons = check_command(command)

    if should_block:
        message = format_blocked_message(command, reasons)
        log_event("BLOCK", command, "; ".join(reasons))

        # Claude Code reads this JSON on stdout:
        # {"decision": "block", "reason": "..."}
        result = {
            "decision": "block",
            "reason": message,
        }
        print(json.dumps(result))
        sys.exit(0)

    # Allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
