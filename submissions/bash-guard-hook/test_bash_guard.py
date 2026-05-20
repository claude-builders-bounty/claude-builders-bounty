#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "bash_guard.py"

CASES = [
    ("ls -la", 0),
    ("git status", 0),
    ("rm -rf dist", 2),
    ("sudo rm -fr /tmp/foo", 2),
    ("psql -c 'DROP TABLE users'", 2),
    ("git push --force origin main", 2),
    ("git push -f", 2),
    ("TRUNCATE events", 2),
    ("DELETE FROM users", 2),
    ("DELETE FROM users WHERE id = 1", 0),
]


def run(command: str) -> int:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/tmp/demo"}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode


def main() -> int:
    failures = []
    for command, expected in CASES:
        got = run(command)
        print(f"{command!r}: expected {expected}, got {got}")
        if got != expected:
            failures.append((command, expected, got))
    if failures:
        print("FAILURES", failures)
        return 1
    print("All bash_guard tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
