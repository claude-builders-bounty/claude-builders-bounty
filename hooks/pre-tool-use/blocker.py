#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands."""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

DESTRUCTIVE_PATTERNS = [
    (re.compile(r'\brm\s+(-rf?|--recursive\s+--force)\s+'), "rm -rf without relative path"),
    (re.compile(r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', re.IGNORECASE), "SQL DROP statement"),
    (re.compile(r'\bgit\s+push\s+.*--force\b'), "Git force push"),
    (re.compile(r'\bTRUNCATE\s+', re.IGNORECASE), "SQL TRUNCATE"),
    (re.compile(r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', re.IGNORECASE), "DELETE without WHERE"),
    (re.compile(r'\bALTER\s+TABLE.*DROP\b', re.IGNORECASE), "ALTER TABLE DROP"),
    (re.compile(r'\bmkfs\.?\b'), "Format filesystem"),
    (re.compile(r'\bchmod\s+-R\s+0{3,4}\s+/'), "Chmod root recursively"),
]

SAFE_OVERRIDES = [
    re.compile(r'\brm\s+(-rf?|--recursive\s+--force)\s+(\.\/|\.\s)'),
    re.compile(r'\bDROP\s+TABLE\s+IF\s+EXISTS\b'),
    re.compile(r'\bDELETE\s+FROM\s+\w+\s+WHERE\b'),
    re.compile(r'\bgit\s+push\s+--force-with-lease\b'),
]


def log_blocked(command, reason, project_path):
    entry = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "command": command[:500],
        "reason": reason,
        "project_path": project_path,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command, project_path):
    for pattern in SAFE_OVERRIDES:
        if pattern.search(command):
            return False
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            log_blocked(command, reason, project_path)
            print(
                f"[BLOCKED] {reason}",
                file=sys.stderr,
            )
            print(
                f"  Command: {command[:200]}",
                file=sys.stderr,
            )
            print(
                f"  Logged to: {LOG_FILE}",
                file=sys.stderr,
            )
            print(
                "  Use --force-with-lease instead of --force, or"
                " add a SAFE_OVERRIDES pattern.",
                file=sys.stderr,
            )
            return True
    return False


def main():
    raw = sys.stdin.read()
    input_data = json.loads(raw)
    tool_use = input_data.get("toolUse", {})
    if tool_use.get("name") != "bash":
        print(json.dumps({"blocked": False}))
        return
    inp = tool_use.get("input", {})
    command = ""
    if isinstance(inp, dict):
        command = inp.get("command", "")
    elif isinstance(inp, list):
        for item in inp:
            if isinstance(item, dict) and "command" in item:
                command = item["command"]
                break
    project_path = os.getcwd()
    blocked = check_command(command, project_path)
    print(json.dumps({"blocked": blocked}))


if __name__ == "__main__":
    main()
