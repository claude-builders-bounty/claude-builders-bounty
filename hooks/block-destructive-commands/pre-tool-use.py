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
    (re.compile(r"drop\s+schema", re.IGNORECASE), "SQL DROP SCHEMA"),
    (
        re.compile(r"\bgit\b.*?\bpush\b.*?\s--force(?!\-\w)", re.IGNORECASE),
        "Git force push (git push --force)",
    ),
    (
        re.compile(r"\bgit\b.*?\bpush\b.*?\s-f\b", re.IGNORECASE),
        "Git force push (git push -f)",
    ),
]

# SQL TRUNCATE — exclude hyphen/underscore command names (e.g. npm run truncate-logs).
TRUNCATE_SQL = re.compile(r"\btruncate\b(?![-/_\w])", re.IGNORECASE)
# Unix truncate(1) uses flag options; avoid blocking file truncation utilities.
TRUNCATE_UTIL = re.compile(r"\btruncate\s+(?:-[a-zA-Z]|--)", re.IGNORECASE)

DELETE_FROM = re.compile(r"delete\s+from", re.IGNORECASE)
WHERE_CLAUSE = re.compile(r"\bwhere\b", re.IGNORECASE)
SHELL_LITERAL = re.compile(r"^\s*(echo|cat|printf|tee)\b", re.IGNORECASE)
GIT_FORCE_REFSPEC = re.compile(
    r"\bgit\b.*?\bpush\b(?:\s+[^\s;|&]+)*\s+\+[^\s;|&]+",
    re.IGNORECASE,
)
DD_DISK = re.compile(r"\bdd\b.*\bof=/dev/", re.IGNORECASE)
FORK_BOMB = re.compile(r":\(\s*\)\s*\{.*:\s*\|.*:.*&.*\}")
MKFS = re.compile(r"\bmkfs(?:\.\w+)?\b", re.IGNORECASE)
DEV_REDIRECT = re.compile(
    r">\s*/dev/(?:sd|hd|nvme|mmcblk|vd|xvd)",
    re.IGNORECASE,
)
WIPEFS = re.compile(r"\bwipefs\b", re.IGNORECASE)
REMOTE_SHELL = re.compile(
    r"\b(?:curl|wget)\b[^\n;|&]*\|\s*(?:ba)?sh\b",
    re.IGNORECASE,
)
GIT_RESET_HARD = re.compile(r"\bgit\b.*?\breset\b.*?\s--hard\b", re.IGNORECASE)
GIT_PUSH_FORCE_CONFIG = re.compile(
    r"-c\s+push\.force(?:\s*=\s*(?P<val>[^\s;|&]+))?",
    re.IGNORECASE,
)
GIT_PUSH_FORCE_CONFIG_FALSE = frozenset({"false", "0", "no", "off", "n"})
CHAIN_SPLIT = re.compile(r"\s*(?:;|&&|\|\|)\s*")


def iter_command_segments(command: str) -> list[str]:
    """Split chained bash commands so each segment is checked independently."""
    return [segment.strip() for segment in CHAIN_SPLIT.split(command) if segment.strip()]


def is_git_force_via_config(command: str) -> bool:
    """True when git -c push.force enables force push (not explicit false values)."""
    if not re.search(r"\bgit\b", command, re.IGNORECASE):
        return False
    if not re.search(r"\bpush\b", command, re.IGNORECASE):
        return False
    for match in GIT_PUSH_FORCE_CONFIG.finditer(command):
        value = (match.group("val") or "").strip().lower().strip("'\"")
        if value not in GIT_PUSH_FORCE_CONFIG_FALSE:
            return True
    return False


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


def check_segment(segment: str) -> str | None:
    if is_rm_rf(segment):
        return "Recursive force delete (rm -rf)"

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(segment):
            return reason

    if TRUNCATE_SQL.search(segment) and not TRUNCATE_UTIL.search(segment):
        return "SQL TRUNCATE"

    if GIT_RESET_HARD.search(segment):
        return "Git hard reset (git reset --hard)"

    if is_git_force_via_config(segment):
        return "Git force push (git -c push.force)"

    if GIT_FORCE_REFSPEC.search(segment):
        return "Git force push (git push +<ref>)"

    if (
        DELETE_FROM.search(segment)
        and not WHERE_CLAUSE.search(segment)
        and not SHELL_LITERAL.match(segment)
    ):
        return "SQL DELETE FROM without WHERE clause"

    if DD_DISK.search(segment):
        return "Disk overwrite (dd of=/dev/*)"

    if FORK_BOMB.search(segment):
        return "Fork bomb"

    if MKFS.search(segment):
        return "Filesystem format (mkfs)"

    if DEV_REDIRECT.search(segment):
        return "Raw device overwrite (> /dev/*)"

    if WIPEFS.search(segment):
        return "Disk signature wipe (wipefs)"

    if REMOTE_SHELL.search(segment):
        return "Remote script execution (curl|sh / wget|sh)"

    return None


def check_command(command: str) -> str | None:
    for segment in iter_command_segments(command):
        reason = check_segment(segment)
        if reason:
            return reason
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
