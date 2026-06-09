#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.
Runs before Claude Code executes Bash tool calls.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "blocklist.json"
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

DEFAULT_BLOCKLIST = {
    "patterns": [
        r"rm\s+(-\w*\s+)*(-[a-zA-Z]*r\w*\s+)?(-[a-zA-Z]*f\w*\s+)?(/\s*$|/\s*$)",
        r"rm\s+-rf\s+/",
        r"rm\s+--recursive\s+--force\s+/",
        r"rm\s+--force\s+--recursive\s+/",
        r"(?i)(?:drop)\s+(?:database|table|schema)",
        r"(?i)(?:truncate)\s+(?:table\s+)?\w+",
        r"(?:mkfs|format\s+filesystem)\b",
        r"dd\s+.*of=/dev/",
        r"sudo\s+rm\s+",
        r"chmod\s+777\s+/",
        r"chown\s+\S+\s+/",
        r"npm\s+publish",
        r"pip\s+upload",
        r"docker\s+(?:rmi|system\s+prune|volume\s+prune)",
        r"(?i)(?:curl|wget)\s+.*\|\s*(?:sh|bash|zsh)",
        r":\(\)\s*\{.*\}",
        r">\s*/etc/(?:passwd|shadow|sudoers|hosts)",
        r"echo\s+.*>\s*/etc/",
        r"(?i)git\s+push\s+.*--force\s+\S*\s*(?:main|master)",
        r"(?i)git\s+push\s+-f\s+\S*\s*(?:main|master)",
    ],
    "allowed_patterns": [
        r"rm\s+-rf\s+(?:\./|~/|\$HOME/|/tmp/|/var/tmp/)",
        r"(?i)truncate\s+(?:table\s+)?(?:temp|test|tmp)_",
    ]
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_BLOCKLIST


def log_blocked(command: str, pattern: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] BLOCKED: command={command!r} matched={pattern!r}\n")


# Critical patterns that, if found ANYWHERE in the full command string, will
# ALWAYS block — no allow-list override is permitted.  These specifically
# target root-filesystem destruction where "/" is the complete target path
# (not a prefix like /tmp/) and must never be bypassable via chaining or
# allow-list misconfiguration.
CRITICAL_FULL_COMMAND_PATTERNS = [
    # rm … /  (root as final argument, possibly followed by comment / chain op)
    r"rm\s+(?:-\w*\s+)*?/\s*(?:$|[;&|\n#])",
    # rm --recursive --force /  (long-flag variants)
    r"rm\s+--recursive\s+--force\s+/\s*(?:$|[;&|\n#])",
    r"rm\s+--force\s+--recursive\s+/\s*(?:$|[;&|\n#])",
]


def _split_chain_commands(command: str) -> list[str]:
    """Split a command string by shell chain operators (; && || |) and newlines.

    This prevents bypasses where a dangerous command is appended after an
    allowed command, e.g. ``rm -rf /tmp/build; rm -rf /``.
    Newlines are also treated as command separators since ``\\n`` acts like
    ``;`` in most shells.
    """
    # Split on shell chain operators: ; && || |  and newlines
    # ;(?!=) avoids splitting inside for-loop arithmetic: for((i=0;i<10;i++))
    parts = re.split(r""";(?!=)|\s*&&\s*|\s*\|\|\s*|\s*\|\s*|\n""", command)
    return [p.strip() for p in parts if p.strip()]


def is_blocked(command: str, config: dict | None = None) -> tuple[bool, str]:
    if config is None:
        config = load_config()

    deny_patterns = config.get("patterns", [])
    allow_patterns = config.get("allowed_patterns", [])

    # --- Layer 0: critical full-command safety net ---
    # Patterns so dangerous they block regardless of any allow-list match.
    # This catches root-filesystem deletion even if an allow-list entry
    # elsewhere in the command string would otherwise bypass the check.
    for pattern in CRITICAL_FULL_COMMAND_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, pattern

    # --- Layer 1: per-sub-command check ---
    # Split on chain operators and check each sub-command independently.
    # The allow-list is applied PER SUB-COMMAND only — a match on one
    # sub-command does NOT exempt a different sub-command from the deny list.
    sub_commands = _split_chain_commands(command)
    for sub in sub_commands:
        for pattern in deny_patterns:
            if re.search(pattern, sub, re.IGNORECASE):
                # Only exempt if THIS specific sub-command matches an allow pattern
                allowed_for_sub = any(
                    re.search(allowed, sub, re.IGNORECASE)
                    for allowed in allow_patterns
                )
                if not allowed_for_sub:
                    return True, pattern

    # --- Layer 2: full-command deny check (pipe-pattern safety net) ---
    # Some deny patterns span across the pipe operator (e.g.
    # ``curl … | sh``).  Splitting on ``|`` breaks those patterns, so we
    # must also scan the un-split command string.  At this point every
    # sub-command has already been individually verified as safe, so the
    # only deny matches here are cross-operator patterns.
    for pattern in deny_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            full_allowed = any(
                re.search(allowed, command, re.IGNORECASE)
                for allowed in allow_patterns
            )
            if not full_allowed:
                return True, pattern

    return False, ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)
    blocked, pattern = is_blocked(command)
    if blocked:
        log_blocked(command, pattern)
        print(f"\n BLOCKED: Destructive command detected!\n"
              f"Pattern matched: {pattern}\n"
              f"Command: {command}\n"
              f"\nIf this is a false positive, add an allowed_pattern to {CONFIG_PATH}")
        sys.exit(2)


if __name__ == "__main__":
    main()
