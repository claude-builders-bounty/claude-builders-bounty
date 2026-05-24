#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Reads the tool-use JSON from stdin and checks if it's a Bash command containing
known destructive patterns. Blocks dangerous operations like rm -rf, DROP TABLE,
git push --force, TRUNCATE, and DELETE FROM without WHERE.

Returns:
  exit 0  — allow the command (no message to stdout = silent pass)
  exit 2  — block the command, stdout is JSON message shown to user

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")


def log_block(command: str, path: str, reasons: list[str]) -> None:
    """Append a blocked-command entry to the log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  command : {command}\n"
        f"  path    : {path}\n"
        f"  reasons : {', '.join(reasons)}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def check_destructive(command: str) -> list[str]:
    """
    Return a list of human-readable reasons why *command* is destructive.
    Empty list means the command is safe.
    """
    reasons: list[str] = []

    # Normalise whitespace so patterns are easier to match
    stripped = command.strip()

    # ── rm -rf (or any scary variant) ──────────────────────────────────
    # Matches: rm -rf, rm -r -f, rm --recursive --force, sudo rm -rf, etc.
    # Handles both combined (-rf, -fr) and separate (-r -f) flag forms.
    if re.search(
        r'\brm\s+.*?('
        r'-[rf]+[rf]*[^a-zA-Z]'           # combined short flags: -rf, -fr, -rfv
        r'|(-r\s.*?-f\b|-f\s.*?-r\b)'     # separate short flags: -r ... -f
        r'|--recursive.*--force|--force.*--recursive'  # long flags
        r')',
        stripped,
    ):
        reasons.append("rm with recursive + force flags")

    # ── DROP TABLE / DROP DATABASE ─────────────────────────────────────
    if re.search(r'\bDROP\s+(TABLE|DATABASE)\b', stripped, re.IGNORECASE):
        reasons.append("DROP TABLE / DATABASE statement")

    # ── TRUNCATE (TABLE) ───────────────────────────────────────────────
    if re.search(r'\bTRUNCATE\b', stripped, re.IGNORECASE):
        reasons.append("TRUNCATE statement")

    # ── DELETE FROM without WHERE ──────────────────────────────────────
    if re.search(r'\bDELETE\s+FROM\b', stripped, re.IGNORECASE):
        if not re.search(r'\bWHERE\b', stripped, re.IGNORECASE):
            reasons.append("DELETE FROM without WHERE clause")

    # ── git push --force / -f (to main/master) ─────────────────────────
    if re.search(r'\bgit\s+push\b', stripped):
        if re.search(r'(-f\b|--force\b|--force-with-lease\b)', stripped):
            reasons.append("git push with force flag")

    return reasons


def main() -> None:
    # Read the tool-use JSON from stdin
    try:
        raw = sys.stdin.read()
        tool_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # If we can't parse stdin, allow the tool call to proceed
        sys.exit(0)

    tool_name = tool_input.get("tool_name", "")

    # Only inspect Bash tool calls — everything else passes through
    if tool_name != "Bash":
        sys.exit(0)

    # The command text can appear in a few places depending on Claude Code version
    command = (
        tool_input.get("tool_input", {}).get("command", "")
        or tool_input.get("command", "")
        or ""
    )

    if not command:
        sys.exit(0)

    # Current working directory context (for logging)
    path = tool_input.get("cwd", "") or tool_input.get("tool_input", {}).get("workdir", "") or os.getcwd()

    reasons = check_destructive(command)
    if not reasons:
        sys.exit(0)  # safe — let it through

    # Block the command
    log_block(command, path, reasons)

    response = {
        "decision": "block",
        "reason": f"Destructive command blocked: {', '.join(reasons)}",
        "details": {
            "command": command,
            "reasons": reasons,
            "suggestion": (
                "If you are sure you want to run this command, temporarily "
                "disable the pre-tool-use hook in your Claude Code settings."
            ),
        },
    }

    print(json.dumps(response, indent=2))
    sys.exit(2)


if __name__ == "__main__":
    main()
