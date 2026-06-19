#!/usr/bin/env python3
"""Exercise the destructive command hook with representative inputs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HOOK = Path(__file__).with_name("pre_tool_use_blocker.py")


def run_hook(command: str) -> subprocess.CompletedProcess[str]:
    payload = {
        "cwd": "/tmp/example-project",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def assert_blocked(command: str) -> None:
    result = run_hook(command)
    assert result.returncode == 2, (command, result.returncode, result.stderr)
    assert "Blocked Bash command:" in result.stderr, result.stderr


def assert_allowed(command: str) -> None:
    result = run_hook(command)
    assert result.returncode == 0, (command, result.returncode, result.stderr)
    assert result.stderr == "", result.stderr


def main() -> int:
    for command in [
        "rm -rf dist",
        "rm -fr ./tmp",
        "git push --force origin main",
        "git push -f",
        "psql -c 'DROP TABLE users'",
        "mysql -e 'TRUNCATE sessions'",
        "psql -c 'DELETE FROM audit_logs'",
    ]:
        assert_blocked(command)

    for command in [
        "rm -r dist",
        "git push origin main",
        "psql -c 'DELETE FROM audit_logs WHERE created_at < now()'",
        "npm test",
        "python -m pytest",
    ]:
        assert_allowed(command)

    print("All hook checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

