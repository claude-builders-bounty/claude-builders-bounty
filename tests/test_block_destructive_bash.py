#!/usr/bin/env python3
"""Basic regression tests for the destructive command hook."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_blocked(command: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_hook(command, Path(tmp))
        assert result.returncode == 2, (command, result.stderr)
        log_path = Path(tmp) / ".claude" / "hooks" / "blocked.log"
        assert log_path.exists()
        entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
        assert entry["command"] == command
        assert entry["project_path"] == "/tmp/example-project"
        assert entry["timestamp"]


def assert_allowed(command: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_hook(command, Path(tmp))
        assert result.returncode == 0, (command, result.stderr)
        assert not (Path(tmp) / ".claude" / "hooks" / "blocked.log").exists()


def test_blocked_commands() -> None:
    for command in (
        "rm -rf node_modules",
        "psql -c 'DROP TABLE users'",
        "git push origin main --force",
        "git push --force-with-lease origin main",
        "sqlite3 app.db 'TRUNCATE sessions'",
        "mysql -e 'DELETE FROM users;'",
    ):
        assert_blocked(command)


def test_allowed_commands() -> None:
    for command in (
        "rm -r build",
        "git push origin main",
        "mysql -e 'DELETE FROM users WHERE id = 1;'",
        "echo hello",
    ):
        assert_allowed(command)


if __name__ == "__main__":
    test_blocked_commands()
    test_allowed_commands()
