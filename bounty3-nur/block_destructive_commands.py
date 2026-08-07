#!/usr/bin/env python3
"""
block_destructive_commands.py — Claude Code PreToolUse hook.

Intercepts Bash tool calls before execution and blocks a curated set of
destructive command patterns (recursive force-remove, forced git pushes,
DROP TABLE, TRUNCATE, and DELETE FROM without a WHERE clause).

Install (see README.md for the 2-command setup):
  1) Copy this file to ~/.claude/hooks/block_destructive_commands.py
  2) Register it as a PreToolUse hook for the Bash tool in your
     Claude Code settings (settings.example.json shows the exact shape).

Behavior:
  - Reads the hook JSON payload from stdin (Claude Code PreToolUse format).
  - If the tool is not Bash (or there's no command), it allows silently.
  - If the command matches a destructive pattern, it:
      * prints a JSON decision on stdout using the modern
        hookSpecificOutput / permissionDecision=deny shape,
      * also exits with code 2 and prints a human-readable reason to
        stderr, for compatibility with the exit-code based hook contract,
      * appends a structured JSONL record to ~/.claude/hooks/blocked.log
        with timestamp, the attempted command, and the project path.
  - Never raises on malformed input — fails closed for logging errors
    but always allows normal, non-matching commands through unharmed.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

PATTERNS = [
    (
        re.compile(r"\brm\s+(?:[^\n;|&]*\s)?-[a-zA-Z-]*r[a-zA-Z-]*f[a-zA-Z-]*\b|"
                   r"\brm\s+(?:[^\n;|&]*\s)?-[a-zA-Z-]*f[a-zA-Z-]*r[a-zA-Z-]*\b|"
                   r"\brm\s+(?:[^\n;|&]*\s)?--recursive\b(?=.*--force)|"
                   r"\brm\s+(?:[^\n;|&]*\s)?--force\b(?=.*--recursive)"),
        "recursive force remove (rm -rf / rm --recursive --force)",
    ),
    (
        re.compile(r"\bgit\s+push\b[^\n;|&]*(?:--force(?:-with-lease)?\b|(?<!\S)-f\b)"),
        "forced git push (git push --force / -f)",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE",
    ),
    (
        re.compile(r"\bTRUNCATE\b(?:\s+TABLE)?\b", re.IGNORECASE),
        "TRUNCATE",
    ),
    (
        re.compile(
            r"\bDELETE\s+FROM\s+[^\s;]+\s*(?:;|$|&&|\|\||\||>)",
            re.IGNORECASE,
        ),
        "DELETE FROM without a WHERE clause",
    ),
]


def find_violation(command: str):
    if not command:
        return None
    for pattern, label in PATTERNS:
        if pattern.search(command):
            if label.startswith("DELETE FROM") and re.search(
                r"\bDELETE\s+FROM\s+[^\s;]+.*\bWHERE\b", command, re.IGNORECASE
            ):
                continue
            return label
    return None


def log_block(command: str, cwd: str, label: str):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempted_command": command,
            "project_path": cwd or os.getcwd(),
            "reason": label,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    cwd = payload.get("cwd", "")

    if tool_name != "Bash" or not command:
        return 0

    label = find_violation(command)
    if not label:
        return 0

    log_block(command, cwd, label)

    reason = (
        f"Blocked by block_destructive_commands.py: this command matches a "
        f"destructive pattern ({label}). If you really need to run it, do it "
        f"manually outside Claude Code, or narrow the command to be explicit "
        f"and reviewed (e.g. add a WHERE clause, avoid --force, target a "
        f"single file instead of a recursive delete)."
    )

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(decision))
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
