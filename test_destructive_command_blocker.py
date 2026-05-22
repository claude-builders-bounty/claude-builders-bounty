#!/usr/bin/env python3
"""Smoke tests for the destructive command hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).parent / ".claude" / "hooks" / "destructive-command-blocker.py"


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {
            "command": command,
            "cwd": "/tmp/project",
        },
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_blocked(command: str, home: Path) -> None:
    result = run_hook(command, home)
    assert result.returncode == 0, (command, result.returncode, result.stderr)
    response = json.loads(result.stdout)
    output = response["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert "Blocked destructive Bash command" in output["permissionDecisionReason"]


def assert_allowed(command: str, home: Path) -> None:
    result = run_hook(command, home)
    assert result.returncode == 0, (command, result.returncode, result.stderr)


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        for command in [
            "rm -rf build",
            "DROP TABLE users",
            "git push --force origin main",
            "TRUNCATE audit_log",
            "DELETE FROM users",
        ]:
            assert_blocked(command, home)

        for command in [
            "ls -la",
            "git status --short",
            "DELETE FROM users WHERE id = 1",
            "rm -r build",
        ]:
            assert_allowed(command, home)

        log_path = home / ".claude" / "hooks" / "blocked.log"
        assert log_path.exists()
        log_text = log_path.read_text(encoding="utf-8")
        assert "attempted_command" in log_text
        assert "/tmp/project" in log_text
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
