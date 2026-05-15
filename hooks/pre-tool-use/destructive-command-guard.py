#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive Bash commands.

Reads JSON from stdin (Claude Code hook protocol), inspects the command,
and either allows (exit 0) or blocks (exit 1) with a clear reason.
Blocked attempts are logged to ~/.claude/hooks/blocked.log

Install:
  mkdir -p ~/.claude/hooks/pre-tool-use
  cp destructive-command-guard.py ~/.claude/hooks/pre-tool-use/destructive-command-guard.py
  chmod +x ~/.claude/hooks/pre-tool-use/destructive-command-guard.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Configuration ────────────────────────────────────────────────

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── Block Rules ──────────────────────────────────────────────────
# Each rule: (name, regex_pattern, explanation)
# Patterns are tested against the full command string

BLOCK_RULES: list[tuple[str, str, str]] = [
    (
        "rm -rf",
        # Matches: rm -rf, rm -fr, rm -r -f, rm --recursive --force, etc.
        r"\brm\b.*(?:"
        r"(?:-[^\s]*[rR][^\s]*[fF])"              # -rf, -fr in a single flag group
        r"|(?:-[^\s]*[fF][^\s]*[rR])"             # -fr, -rf reversed in a single flag
        r"|(?:-[^\s]*[rR].*-[^\s]*[fF])"          # -r ... -f (separate flags)
        r"|(?:-[^\s]*[fF].*-[^\s]*[rR])"          # -f ... -r (separate flags, reversed)
        r"|(?:--recursive.*--force)"               # long form
        r"|(?:--force.*--recursive)"               # long form reversed
        r")",
        "Recursive forced deletion (rm -rf) can irreversibly destroy project or system files.",
    ),
    (
        "DROP TABLE",
        r"\bdrop\s+table\b",
        "DROP TABLE permanently removes a database table and all its data.",
    ),
    (
        "TRUNCATE",
        r"\btruncate\s+(?:table\s+)?\w",
        "TRUNCATE deletes all rows from a table without logging individual row deletions.",
    ),
    (
        "git push --force",
        # Matches: git push --force, git push -f, git push --force-with-lease
        r"\bgit\s+push\b.*"
        r"(?:--force(?!-with-lease\b)|--force-with-lease|-f\b)",
        "Force pushing rewrites remote branch history and can destroy collaborators' work.",
    ),
    (
        "DELETE FROM without WHERE",
        # Matches DELETE FROM that doesn't contain WHERE (case-insensitive)
        r"\bdelete\s+from\s+\w+"
        r"(?:(?!\bwhere\b).)*$",
        "DELETE FROM without a WHERE clause removes all rows from the table.",
    ),
]


# ── Logging ──────────────────────────────────────────────────────

def log_block(rule_name: str, command: str, cwd: str, reason: str) -> None:
    """Append a blocked attempt to the log file."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = (
        f"[{timestamp}]\n"
        f"  Rule:     {rule_name}\n"
        f"  Command:  {command}\n"
        f"  CWD:      {cwd}\n"
        f"  Reason:   {reason}\n"
        f"{'─' * 60}\n"
    )
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        # If we can't log, still block — security first
        pass


# ── Payload parsing ──────────────────────────────────────────────

def load_payload() -> dict[str, Any]:
    """Parse the JSON payload from stdin (Claude Code hook protocol)."""
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: treat raw input as a bare command
        return {"tool_input": {"command": raw}}


def extract_command(payload: dict[str, Any]) -> str:
    """Extract the command string from a hook payload."""
    # Standard path: payload.tool_input.command
    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        return str(tool_input.get("command", ""))
    return ""


def extract_cwd(payload: dict[str, Any]) -> str:
    """Extract working directory from the hook payload."""
    return payload.get("cwd", "") or payload.get("working_dir", "") or os.getcwd()


def extract_tool_name(payload: dict[str, Any]) -> str:
    """Extract the tool name from the hook payload."""
    return str(payload.get("tool_name", "") or payload.get("tool", ""))


# ── Core logic ───────────────────────────────────────────────────

def check_command(command: str) -> tuple[bool, str, str]:
    """Check a command against all block rules.

    Returns (should_block: bool, rule_name: str, reason: str)
    """
    if not command or not command.strip():
        return False, "", ""

    command_clean = command.strip()

    for rule_name, pattern, reason in BLOCK_RULES:
        if re.search(pattern, command_clean, re.IGNORECASE | re.DOTALL):
            return True, rule_name, reason

    return False, "", ""


def main() -> int:
    payload = load_payload()

    # Only intercept Bash tool calls
    tool_name = extract_tool_name(payload)
    if tool_name and tool_name.lower() != "bash":
        return 0  # Not a bash command, allow

    command = extract_command(payload)
    if not command:
        return 0  # No command to check, allow

    cwd = extract_cwd(payload)

    should_block, rule_name, reason = check_command(command)

    if not should_block:
        return 0  # Safe command, allow

    # ── Block the command ──
    log_block(rule_name, command, cwd, reason)

    # Output a clear message to Claude (stdout is shown to the model)
    print(
        f"⛔ BLOCKED — {rule_name}\n"
        f"\n"
        f"  Command: {command}\n"
        f"  Reason:  {reason}\n"
        f"\n"
        f"  This command was intercepted by the destructive-command-guard hook.\n"
        f"  If you are certain this command is safe, re-run it manually in a\n"
        f"  terminal outside of Claude Code, or temporarily disable this hook.\n"
        f"\n"
        f"  Logged to: {LOG_PATH}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
