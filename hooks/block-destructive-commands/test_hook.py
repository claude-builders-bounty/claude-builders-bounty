#!/usr/bin/env python3
"""
Test suite for the pre-tool-use destructive command blocker hook.
Sends simulated Claude Code hook payloads via stdin and verifies
that dangerous commands are blocked (exit 2) and safe ones pass (exit 0).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "pre_tool_use.py"

SHOULD_BLOCK = [
    ("rm -rf /tmp/myproject", "rm -rf"),
    ("rm -fr dist", "rm -rf"),
    ("rm --recursive --force build/", "rm --recursive --force"),
    ("sudo rm -rf /", "rm -rf"),
    ("DROP TABLE users;", "DROP TABLE"),
    ("DROP DATABASE production;", "DROP DATABASE"),
    ("TRUNCATE orders;", "TRUNCATE"),
    ("TRUNCATE TABLE inventory;", "TRUNCATE"),
    ("git push origin main --force", "git push --force"),
    ("git push origin main -f", "git push --force"),
    ("git push --force-with-lease origin main", "git push --force"),
    ("DELETE FROM sessions;", "DELETE FROM without WHERE"),
    ("DELETE FROM users", "DELETE FROM without WHERE"),
]

SHOULD_PASS = [
    "ls -la",
    "npm run build",
    "git commit -m 'fix bug'",
    "git push origin main",
    "DELETE FROM users WHERE id = 5;",
    "rm single_file.txt",
    "rm -r build/output",
    "cat README.md",
    "echo 'hello world'",
    "pip install requests",
    "python3 -m pytest tests/",
    "git push origin feature-branch",
]


def run_hook(command: str) -> tuple[int, str]:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/test-project",
    })
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stderr.strip()


def main() -> int:
    passed = 0
    failed = 0

    print("=" * 70)
    print("TEST SUITE: Pre-Tool-Use Destructive Command Blocker")
    print("=" * 70)

    for cmd, label in SHOULD_BLOCK:
        code, stderr = run_hook(cmd)
        if code == 2:
            passed += 1
            print(f"  PASS [BLOCKED] {label:40s} | {cmd}")
        else:
            failed += 1
            print(f"  FAIL [BLOCKED] expected exit 2, got {code}  | {cmd}")

    for cmd in SHOULD_PASS:
        code, stderr = run_hook(cmd)
        if code == 0:
            passed += 1
            print(f"  PASS [ALLOWED] {'(safe command)':40s} | {cmd}")
        else:
            failed += 1
            print(f"  FAIL [ALLOWED] expected exit 0, got {code}  | {cmd}")

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
