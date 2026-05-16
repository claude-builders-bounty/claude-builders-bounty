#!/usr/bin/env python3
"""Smoke tests for destructive_command_blocker.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).with_name("destructive_command_blocker.py")

BLOCKED = [
    "rm -rf build",
    "DROP TABLE users;",
    "git push --force origin main",
    "git push -f origin main",
    "git push --force-with-lease origin main",
    "TRUNCATE users;",
    "DELETE FROM users;",
]

ALLOWED = [
    "rm -r build",
    "git push origin main",
    "DELETE FROM users WHERE id = 1;",
    "SELECT * FROM users;",
]


def run(command: str) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/destructive-command-blocker-test",
    })
    env = os.environ.copy()
    env["HOME"] = tempfile.mkdtemp(prefix="destructive-command-blocker-home-")
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def main() -> int:
    failures: list[str] = []

    for command in BLOCKED:
        result = run(command)
        if result.returncode == 0 or "Blocked destructive Bash command" not in result.stderr:
            failures.append(f"Expected block for {command!r}; got rc={result.returncode}, stderr={result.stderr!r}")

    for command in ALLOWED:
        result = run(command)
        if result.returncode != 0:
            failures.append(f"Expected allow for {command!r}; got rc={result.returncode}, stderr={result.stderr!r}")

    if failures:
        print("FAIL")
        print("\n".join(failures))
        return 1

    print(f"PASS: {len(BLOCKED)} blocked, {len(ALLOWED)} allowed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
