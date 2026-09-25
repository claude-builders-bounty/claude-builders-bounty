#!/usr/bin/env python3
"""Replay the hook against fixed payloads. Exits 1 if any case disagrees."""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pre_tool_use.py")
CASES = [
    ("safe ls", 0, "ls -la", False),
    ("safe git", 0, "git status", False),
    ("delete with where", 0, "DELETE FROM users WHERE id = 3", False),
    ("rm -rf", 2, "rm -rf /tmp/proj", True),
    ("drop table", 2, "DROP TABLE users", True),
    ("truncate", 2, "TRUNCATE orders", True),
    ("force push", 2, "git push --force origin main", True),
    ("delete all", 2, "DELETE FROM users", True),
]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        log = os.path.join(tmp, "blocked.log")
        env = dict(os.environ, HOOK_LOG=log)
        failed = 0
        for name, expect, command, logged in CASES:
            payload = json.dumps({"tool_input": {"command": command}, "cwd": "/tmp/proj"})
            result = subprocess.run(
                [sys.executable, HOOK],
                input=payload,
                text=True,
                capture_output=True,
                env=env,
            )
            text = open(log, encoding="utf-8").read() if os.path.exists(log) else ""
            present = command in text
            ok = result.returncode == expect and present == logged
            print(("PASS " if ok else "FAIL ") + name)
            failed += not ok
        return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
