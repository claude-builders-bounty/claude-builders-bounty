#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
import sys


PATTERNS = [
    (re.compile(r"\brm\s+-rf\b", re.IGNORECASE), "rm -rf is blocked"),
    (re.compile(r"\bdrop\s+table\b", re.IGNORECASE), "DROP TABLE is blocked"),
    (re.compile(r"\btruncate\b", re.IGNORECASE), "TRUNCATE is blocked"),
    (re.compile(r"\bgit\s+push\b.*\b--force\b", re.IGNORECASE), "git push --force is blocked"),
    (re.compile(r"\bgit\s+push\b.*\s-f\b", re.IGNORECASE), "git push -f is blocked"),
    (
        re.compile(r"\bdelete\s+from\b(?![^;]*\bwhere\b)", re.IGNORECASE | re.DOTALL),
        "DELETE FROM without WHERE is blocked",
    ),
]


def log_block(cwd: str, command: str) -> None:
    log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    with open(log_path, "a", encoding="utf-8") as fp:
        fp.write(f"{timestamp}\t{command}\t{cwd}\n")


def main() -> int:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    cwd = payload.get("cwd", os.getcwd())

    for pattern, reason in PATTERNS:
        if pattern.search(command):
            log_block(cwd, command)
            sys.stderr.write(
                f"Blocked dangerous Bash command: {reason}. Command: {command}\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
