#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code.

Blocks destructive bash commands BEFORE they are executed.

Installation (2 commands):
    mkdir -p ~/.claude/hooks
    cp pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py

Then add to ~/.claude/settings.json:
    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Bash",
            "hooks": [
              { "type": "command", "command": "~/.claude/hooks/pre-tool-use.py" }
            ]
          }
        ]
      }
    }

Input (JSON on stdin, Claude Code hook format):
    {
      "tool_name": "Bash",
      "tool_input": { "command": "rm -rf node_modules" },
      "cwd": "/path/to/project"
    }

Output:
    Blocked -> {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                "decision": "block", "reason": "..."}} (exit code 2)
    Allowed -> empty JSON object (exit code 0)
"""

import json
import os
import re
import sys
from datetime import datetime

# --- Configuration ---------------------------------------------------------
HOOK_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOK_DIR, "blocked.log")

# Patterns that are ALWAYS blocked (regex, case-insensitive).
BLOCK_PATTERNS = [
    # rm -rf / dangerous recursive deletes
    r"\brm\s+(-[a-z]*r[a-z]*f[a-z]*|-rf)\s+[^\n;|&]*\/",      # rm -rf /something
    r"\brm\s+-rf\b",                                          # rm -rf anywhere
    # destructive SQL
    r"\bDROP\s+TABLE\b",
    r"\bTRUNCATE(?:\s+TABLE)?\b",
    r"\bDELETE\s+FROM\b(?![\s\S]*(?:WHERE|LIMIT)\b)",
    # nuclear filesystem commands
    r"\b(mkfs|format|dd)\b.*\b(?:/dev/|boot)",
    r"\bchmod\s+-R\s+777\s+/",
]

# git push --force is handled separately (needs --force-with-lease awareness).
FORCE_PUSH_PATTERN = re.compile(r"\bgit\s+push\b", re.IGNORECASE)
FORCE_WITH_LEASE = re.compile(r"--force-with-lease\b", re.IGNORECASE)
FORCE_FLAG = re.compile(r"(?:--force\b|(?<![\w-])-f\b)", re.IGNORECASE)

# Pattern compiled once.
_BLOCKED = [(re.compile(p, re.IGNORECASE), p) for p in BLOCK_PATTERNS]


def is_force_push(command: str) -> bool:
    """True when the command is a git push using --force / -f,
    but NOT the safe --force-with-lease variant."""
    if not FORCE_PUSH_PATTERN.search(command):
        return False
    if FORCE_WITH_LEASE.search(command):
        return False
    return bool(FORCE_FLAG.search(command))


def is_blocked(command: str) -> bool:
    """Return True when the command matches a destructive pattern."""
    if is_force_push(command):
        return True
    for pattern, _ in _BLOCKED:
        if pattern.search(command):
            return True
    return False


def log_block(command: str, project_path: str) -> None:
    """Append a blocked attempt to ~/.claude/hooks/blocked.log."""
    try:
        os.makedirs(HOOK_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(
                "%s | project=%s | blocked=%s\n"
                % (
                    datetime.now().isoformat(timespec="seconds"),
                    project_path,
                    command.replace("\n", " ").strip(),
                )
            )
    except OSError:
        # Logging must never crash the hook; the block decision already happened.
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        # No valid input -> do not interfere with normal operation.
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    command = str(tool_input.get("command", ""))
    cwd = payload.get("cwd") or os.getcwd()

    # Only inspect Bash tool calls.
    if tool_name != "Bash" or not command:
        return 0

    if is_blocked(command):
        log_block(command, cwd)
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "decision": "block",
                        "reason": (
                            "This bash command was blocked by the safety hook: "
                            "it matches a destructive pattern (rm -rf, git push --force, "
                            "DROP TABLE, TRUNCATE, or DELETE FROM without WHERE). "
                            "If this is intentional, rephrase the command to be more "
                            "specific or add an explicit safety check."
                        ),
                    }
                }
            )
        )
        # Claude Code: exit code 2 tells the model the decision is a block.
        return 2

    # Allow: print an empty JSON object so Claude Code can continue.
    print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
