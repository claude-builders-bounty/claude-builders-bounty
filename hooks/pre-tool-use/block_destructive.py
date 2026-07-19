#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.

Install: cp block_destructive.py ~/.claude/hooks/pre-tool-use
"""

import json
import logging
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
DESTRUCTIVE_PATTERNS = [
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bgit\s+push\s+--force\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\b(?!\s+\w+\s+WHERE)", re.IGNORECASE),
]


def setup_logging():
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(message)s",
    )


def is_blocked_command(tool_input: dict) -> tuple[bool, str]:
    command = tool_input.get("command", "")
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return True, str(pattern.pattern)
    return False, ""


def main():
    setup_logging()

    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({"is_blocked": False}))
        sys.exit(0)

    tool_use = payload.get("tool_use", {})
    tool_input = tool_use.get("input", {})

    blocked, pattern = is_blocked_command(tool_input)

    if blocked:
        command = tool_input.get("command", "unknown")
        project = os.getcwd()
        timestamp = datetime.now().isoformat()

        logging.info(f"BLOCKED | cmd={command} | pattern={pattern} | project={project}")

        result = {
            "is_blocked": True,
            "reason": (
                f"Command blocked by pre-tool-use hook.\n"
                f"Matched destructive pattern: {pattern}\n"
                f"Attempted: {command}\n"
                f"Logged to: {LOG_FILE}"
            ),
        }
        print(json.dumps(result))
        sys.exit(0)

    print(json.dumps({"is_blocked": False}))


if __name__ == "__main__":
    main()
