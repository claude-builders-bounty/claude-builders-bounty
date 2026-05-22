#!/usr/bin/env python3
"""Smoke tests for block-dangerous-bash.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HOOK = Path(__file__).with_name("block-dangerous-bash.py")


def run_hook(command: str) -> dict:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        env = os.environ.copy()
        env["CLAUDE_HOOK_LOG_PATH"] = str(Path(tmpdir) / "blocked.log")
        completed = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
    return json.loads(completed.stdout)


def permission(output: dict) -> str:
    return output["hookSpecificOutput"]["permissionDecision"]


def main() -> int:
    blocked = [
        "rm -rf /tmp/example",
        "rm -r -f /tmp/example",
        "git push --force origin main",
        "psql -c 'DROP TABLE users'",
        "psql -c 'TRUNCATE users'",
        "psql -c 'DELETE FROM users'",
    ]
    allowed = [
        "ls -la",
        "git status --short",
        "rm -r /tmp/example",
        "psql -c 'DELETE FROM users WHERE id = 1'",
    ]

    for command in blocked:
        assert permission(run_hook(command)) == "deny", command

    for command in allowed:
        assert permission(run_hook(command)) == "allow", command

    print("All hook smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
