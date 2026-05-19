#!/usr/bin/env python3
"""Smoke tests for block_destructive_bash.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HOOK = Path(__file__).with_name("block_destructive_bash.py")


def run(command: str) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_input": {"command": command}, "cwd": "/tmp/example"})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, text=True, capture_output=True, check=False)


def test_blocks_required_patterns() -> None:
    for command in [
        "rm -rf build",
        "psql -c 'DROP TABLE users'",
        "git push --force origin main",
        "sqlite3 app.db 'TRUNCATE sessions'",
        "sqlite3 app.db 'DELETE FROM users;'",
    ]:
        result = run(command)
        assert result.returncode != 0, command
        assert "Blocked destructive bash command" in result.stderr


def test_allows_safe_commands() -> None:
    for command in [
        "ls -la",
        "git push origin feature",
        "sqlite3 app.db 'DELETE FROM users WHERE id = 1;'",
    ]:
        result = run(command)
        assert result.returncode == 0, command


if __name__ == "__main__":
    test_blocks_required_patterns()
    test_allows_safe_commands()
    print("ok")
