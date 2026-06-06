#!/usr/bin/env python3
"""Claude Code PreToolUse hook — blocks destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

BLOCKED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"rm\s+--recursive\s+--force", re.IGNORECASE), "Recursive force delete (rm --recursive --force)"),
    (re.compile(r"drop\s+table", re.IGNORECASE), "SQL DROP TABLE"),
    (re.compile(r"drop\s+database", re.IGNORECASE), "SQL DROP DATABASE"),
    (
        re.compile(r"\bgit\b.*?\bpush\b.*?\s--force(?!\-\w)", re.IGNORECASE),
        "Git force push (git push --force)",
    ),
    (
        re.compile(r"\bgit\b.*?\bpush\b.*?\s-f\b", re.IGNORECASE),
        "Git force push (git push -f)",
    ),
    (re.compile(r"\btruncate\b", re.IGNORECASE), "SQL TRUNCATE"),
]

DELETE_FROM = re.compile(r"delete\s+from", re.IGNORECASE)
WHERE_CLAUSE = re.compile(r"\bwhere\b", re.IGNORECASE)
SHELL_LITERAL = re.compile(r"^\s*(echo|cat|printf|tee)\b", re.IGNORECASE)
DD_DISK = re.compile(r"\bdd\b.*\bof=/dev/", re.IGNORECASE)
FORK_BOMB = re.compile(r":\(\s*\)\s*\{.*:\s*\|.*:.*&.*\}")


def is_rm_rf(command: str) -> bool:
    """True when rm uses both recursive (-r) and force (-f) flags in any order."""
    for match in re.finditer(r"\brm\s+((?:-\S+\s+)*-\S+)", command):
        flags = "".join(re.findall(r"-([A-Za-z]+)", match.group(1))).lower()
        if "r" in flags and "f" in flags:
            return True
    return False


def log_blocked_attempt(command: str, project_path: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(
            f"[{timestamp}] Command: {command} | Project: {project_path}\n"
        )


def deny(reason: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def check_command(command: str) -> str | None:
    if is_rm_rf(command):
        return "Recursive force delete (rm -rf)"

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            return reason

    if (
        DELETE_FROM.search(command)
        and not WHERE_CLAUSE.search(command)
        and not SHELL_LITERAL.match(command)
    ):
        return "SQL DELETE FROM without WHERE clause"

    if DD_DISK.search(command):
        return "Disk overwrite (dd of=/dev/*)"

    if FORK_BOMB.search(command):
        return "Fork bomb"

    return None


def main() -> None:
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            sys.exit(0)

        data = json.loads(raw_input)
        if data.get("tool_name") != "Bash":
            sys.exit(0)

        tool_input = data.get("tool_input") or {}
        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)

        project_path = data.get("cwd") or os.getcwd()
        block_reason = check_command(command)
        if block_reason:
            log_blocked_attempt(command, project_path)
            deny(
                f"{block_reason} blocked. "
                f"Run this command directly in your terminal if you truly need it."
            )
    except Exception:
        # Never block legitimate commands because the hook failed unexpectedly.
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
