#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts Bash tool calls before execution and blocks commands matching
known destructive patterns. Logs all blocked attempts with timestamps.

Exit codes (per Claude Code hook protocol):
  0 = allow  (command is safe)
  2 = block  (command is destructive; reason printed to stderr)

Called by Claude Code with tool invocation JSON on stdin.
"""

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_PATH = Path(os.environ.get(
    "HOOK_BLOCKED_LOG",
    Path.home() / ".claude" / "hooks" / "blocked.log",
))

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# SQL / Git patterns — regex works well here because the syntax is rigid
REGEX_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # ── SQL: DROP TABLE ──────────────────────────────────────────────────
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE is blocked to prevent accidental schema destruction.",
    ),
    # ── SQL: TRUNCATE ────────────────────────────────────────────────────
    (
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?", re.IGNORECASE),
        "TRUNCATE is blocked to prevent accidental table data wipe.",
    ),
    # ── SQL: DELETE FROM without WHERE ───────────────────────────────────
    # Matches "DELETE FROM <table>" only when NOT followed by WHERE.
    # Uses a negative lookahead after capturing the table name.
    (
        re.compile(
            r"\bDELETE\s+FROM\s+\S+"    # DELETE FROM <table>
            r"(?!"                       # negative lookahead:
            r"[\s;]*\s+WHERE\b"          #   whitespace + WHERE keyword
            r")",
            re.IGNORECASE,
        ),
        "DELETE FROM without a WHERE clause is blocked to prevent deleting all rows.",
    ),
    # ── Git: force push ─────────────────────────────────────────────────
    (
        re.compile(
            r"\bgit\s+push\b"           # git push
            r"[^\n]*?"                   # any intervening args/flags
            r"(?:--force(?:-with-lease)?|-f)\b",  # force flag
            re.IGNORECASE,
        ),
        "Force push (git push --force/-f) is blocked to prevent overwriting remote history.",
    ),
]


def check_rm_pattern(command: str) -> Optional[str]:
    """
    Detect 'rm -rf' / 'rm -fr' style commands using token analysis.

    Handles:
      rm -rf /path
      rm -fr /path
      rm -rfv /path
      sudo rm -rf /path
      rm -r --interactive=never -f /path   (separate -r and -f flags)

    Does NOT flag:
      rm -f file         (force without recursive — safe single-file delete)
      rm -r dir/         (recursive without force — prompts before deleting)
      rm file            (plain delete)
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        # Malformed quoting — fall back to simple split
        tokens = command.split()

    if not tokens:
        return None

    # Strip leading 'sudo' / 'doas'
    while tokens and tokens[0] in ("sudo", "doas"):
        tokens = tokens[1:]

    if not tokens or tokens[0] != "rm":
        return None

    # Collect all flag characters from -x style tokens
    has_recursive = False
    has_force = False
    has_target = False

    for tok in tokens[1:]:
        if tok == "--":
            # Everything after -- is a file target
            has_target = len(tokens[tokens.index("--") + 1:]) > 0
            break
        if tok == "--recursive" or tok == "--force":
            if tok == "--recursive":
                has_recursive = True
            else:
                has_force = True
        elif tok.startswith("-") and len(tok) > 1 and tok[1] != "-":
            flags = tok[1:]  # strip leading dash
            if "r" in flags or "R" in flags:
                has_recursive = True
            if "f" in flags:
                has_force = True
        elif not tok.startswith("-"):
            has_target = True

    if has_recursive and has_force and has_target:
        return (
            "Recursive forced deletion (rm -rf) is blocked to prevent "
            "accidental data loss. Use 'rm -r' (without -f) to get "
            "confirmation prompts, or delete specific files individually."
        )

    return None


def check_command(command: str) -> Optional[str]:
    """Check a command against all blocked patterns. Return reason or None."""
    # 1) rm -rf check (token-based)
    reason = check_rm_pattern(command)
    if reason:
        return reason

    # 2) Regex-based checks (SQL, git)
    for pattern, reason in REGEX_PATTERNS:
        if pattern.search(command):
            return reason

    return None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_blocked(command: str, reason: str, project: str) -> None:
    """Append a blocked-attempt entry to the log file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = (
        f"{timestamp} | BLOCKED: {command.strip()}\n"
        f"  reason={reason}\n"
        f"  project={project}\n\n"
    )
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except OSError:
        # Non-fatal: blocking still works even if logging fails
        pass


# ---------------------------------------------------------------------------
# Payload extraction
# ---------------------------------------------------------------------------

def extract_command(payload: dict) -> Optional[str]:
    """Pull the command string from the Claude Code hook payload."""
    tool_input = payload.get("tool_input", {})
    return tool_input.get("command") if isinstance(tool_input, dict) else None


def extract_project(payload: dict) -> str:
    """Best-effort project/cwd extraction from the payload."""
    for key_path in [
        ("tool_input", "cwd"),
        ("cwd",),
        ("project_path",),
    ]:
        obj = payload
        for key in key_path:
            obj = obj.get(key) if isinstance(obj, dict) else None
        if isinstance(obj, str):
            return obj
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Read payload from stdin
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        # Malformed input → don't block, pass through
        sys.exit(0)

    command = extract_command(payload)

    # Not a bash command or no command string → nothing to check
    if not command:
        sys.exit(0)

    reason = check_command(command)

    if reason is None:
        # Command is safe — allow it
        sys.exit(0)

    # ── Block the command ────────────────────────────────────────────────
    project = extract_project(payload)
    log_blocked(command, reason, project)

    # Print a clear, actionable message to stderr.
    # Claude Code surfaces stderr to the model so it can adjust its approach.
    message = (
        f"⚠️  BLOCKED destructive command:\n"
        f"  Command: {command.strip()}\n"
        f"  Reason:  {reason}\n"
        f"  Logged to: {LOG_PATH}\n\n"
        f"  Please use a safer alternative.\n"
    )
    print(message, file=sys.stderr)

    # Exit code 2 tells Claude Code to block the tool call and show stderr
    sys.exit(2)


if __name__ == "__main__":
    main()
