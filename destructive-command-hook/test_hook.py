#!/usr/bin/env python3
"""Smoke tests for block_destructive_bash.py without requiring Claude Code."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HOOK = Path(__file__).with_name("block_destructive_bash.py")


def run_hook(command: str, home: str) -> dict:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": "/tmp/example-project",
        "tool_input": {"command": command},
    }
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "HOME": home},
    )
    return json.loads(result.stdout)


def decision(output: dict) -> str:
    return output["hookSpecificOutput"]["permissionDecision"]


def main() -> int:
    blocked = [
        "rm -rf node_modules",
        "DROP TABLE users;",
        "git push --force origin main",
        "git push -f",
        "TRUNCATE TABLE sessions;",
        "DELETE FROM users;",
    ]
    allowed = [
        "ls -la",
        "rm -r build",
        "git push origin main",
        "DELETE FROM users WHERE id = ?;",
        "npm run build",
    ]

    with tempfile.TemporaryDirectory() as home:
        for command in blocked:
            assert decision(run_hook(command, home)) == "deny", command
        for command in allowed:
            assert decision(run_hook(command, home)) == "allow", command

    print("All destructive-command hook tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
