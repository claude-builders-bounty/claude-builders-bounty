#!/usr/bin/env python3
"""Tests for block_destructive_commands.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "block_destructive_commands.py"


def run_hook(command: str, log_path: Path) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_input": {"command": command}, "cwd": "C:/repo"})
    return subprocess.run(
        [sys.executable, str(HOOK), "--log", str(log_path)],
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def assert_blocked(command: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "blocked.log"
        result = run_hook(command, log_path)
        assert result.returncode == 2, result.stdout + result.stderr
        response = json.loads(result.stdout)
        assert response["decision"] == "block"
        log_lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(log_lines) == 1
        log_record = json.loads(log_lines[0])
        assert log_record["command"] == command
        assert log_record["project_path"] == "C:/repo"


def assert_allowed(command: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "blocked.log"
        result = run_hook(command, log_path)
        assert result.returncode == 0, result.stdout + result.stderr
        response = json.loads(result.stdout)
        assert response["decision"] == "allow"
        assert not log_path.exists()


def test_blocks_required_patterns() -> None:
    assert_blocked("rm -rf dist")
    assert_blocked("git push origin main --force")
    assert_blocked("psql -c 'DROP TABLE users'")
    assert_blocked("TRUNCATE audit_log")
    assert_blocked("DELETE FROM users")


def test_allows_safe_commands() -> None:
    assert_allowed("git status --short")
    assert_allowed("npm test")
    assert_allowed("DELETE FROM users WHERE id = 1")
    assert_allowed("rm -r dist")


if __name__ == "__main__":
    test_blocks_required_patterns()
    test_allows_safe_commands()
    print("ok")
