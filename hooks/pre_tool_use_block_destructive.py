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


def is_blocked(command: str, config: dict | None = None) -> tuple[bool, str]:
    if config is None:
        config = load_config()
    for allowed in config.get("allowed_patterns", []):
        if re.search(allowed, command, re.IGNORECASE):
            return False, ""
    for pattern in config.get("patterns", []):
        if re.search(pattern, command, re.IGNORECASE):
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
